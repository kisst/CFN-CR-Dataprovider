import json
import logging
import boto3
import cfnresponse

log = logging.getLogger()
# log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)

def cfn_failed(event, context):
    """ Short function for signaling CFN about fault """
    resp_data = {}
    resp = cfnresponse.FAILED
    cfnresponse.send(event, context, resp, resp_data)


def flat_out_filter(cfn_filter):
    """ Flat out the filter structure """
    flat_filter = []
    for key in cfn_filter:
        condition = {}
        condition["Name"] = key
        condition["Values"] = []
        condition["Values"].append(cfn_filter[key])
        flat_filter.append(condition)
    return flat_filter


def flat_out_dict(dictionary, flat=dict(), prefix=""):
    """ Flat out dict so all attributes can be accessed with GetAtt """
    for key, value in dictionary.items():
        if prefix == "":
            key = str(key)
        else:
            key = prefix + "." + str(key)
        if isinstance(value, dict):
            flat_out_dict(value, flat, key)
        else:
            flat[key] = str(value)
    return flat


def handler(event, context):
    """Main Lambda Function"""
    # default is failed with no data
    log.debug("Received event: %s", json.dumps(event))
    filters = flat_out_filter(event["ResourceProperties"]["Filter"])
    filters_raw = event["ResourceProperties"]["Filter"]
    log.debug("Where filters are: %s", filters)

    if event["RequestType"] == "Delete":
        # Nothing to do here, let's signal CFN that we are done
        resp = cfnresponse.SUCCESS
        cfnresponse.send(event, context, resp, {})
        return

    if event["ResourceType"] == "Custom::Subnet":
        log.debug("Subnet lookup")
        ec2 = boto3.client("ec2")
        search = ec2.describe_subnets(Filters=filters)
        if len(search["Subnets"]) == 1:
            subnet = search["Subnets"][0]
            resp = cfnresponse.SUCCESS
            cfnresponse.send(
                event, context, resp, subnet, subnet["SubnetId"]
            )
        else:
            cfn_failed(event, context)

    elif event["ResourceType"] == "Custom::VPC":
        log.debug("VPC lookup")
        ec2 = boto3.client("ec2")
        search = ec2.describe_vpcs(Filters=filters)
        if len(search["Vpcs"]) == 1:
            vpc = search["Vpcs"][0]
            resp = cfnresponse.SUCCESS
            cfnresponse.send(event, context, resp, vpc, vpc["VpcId"])
        else:
            cfn_failed(event, context)

    elif event["ResourceType"] == "Custom::R53HostedZone":
        log.debug("R53 Hosted Zone lookup")
        r53 = boto3.client("route53")
        if "HostedZoneId" in filters_raw:
            zone_id = filters_raw["HostedZoneId"]
        elif "DNSName" in filters_raw:
            print(filters_raw["DNSName"])
            zone_list = r53.list_hosted_zones_by_name(DNSName=filters_raw["DNSName"])
            if not zone_list:
                log.error("Error on R53 lookup")
                cfn_failed(event, context)
            zones = []
            for zone in zone_list["HostedZones"]:
                private = str(zone["Config"]["PrivateZone"]).lower()
                if private == filters_raw["PrivateZone"].lower():
                    zones.append(zone)
            if len(zones) == 1:
                zone_id = zones[0]["Id"].split("/")[2]
            else:
                log.error("Too many or too few matches")
                cfn_failed(event, context)
        else:
            log.error("Unsupported R53 filters")
            cfn_failed(event, context)
        zone = r53.get_hosted_zone(Id=zone_id)
        if zone:
            resp = cfnresponse.SUCCESS
            cfnresponse.send(
                event, context, resp, flat_out_dict(zone), zone_id
            )
        else:
            cfn_failed(event, context)

    else:
        log.error("Unsupported resource lookup")
        cfn_failed(event, context)
