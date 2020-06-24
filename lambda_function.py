import json
import logging
import boto3
import cfnresponse

log = logging.getLogger()
# log.setLevel(logging.INFO)
log.setLevel(logging.DEBUG)


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
    response_data = {}
    response_status = cfnresponse.FAILED

    log.debug("Received event: %s", json.dumps(event))
    filters = flat_out_filter(event["ResourceProperties"]["Filter"])
    filters_raw = event["ResourceProperties"]["Filter"]
    log.debug("Where filters are: %s", filters)

    if event["RequestType"] == "Delete":
        # Nothing to do here, let's signal CFN that we are done
        response_status = cfnresponse.SUCCESS
        cfnresponse.send(event, context, response_status, response_data)
        return

    if event["ResourceType"] == "Custom::Subnet":
        log.debug("Subnet lookup")
        ec2 = boto3.client("ec2")
        search = ec2.describe_subnets(Filters=filters)
        if len(search["Subnets"]) == 1:
            subnet = search["Subnets"][0]
            response_status = cfnresponse.SUCCESS
            cfnresponse.send(
                event, context, response_status, subnet, subnet["SubnetId"]
            )
        else:
            cfnresponse.send(event, context, response_status, response_data)

    elif event["ResourceType"] == "Custom::VPC":
        log.debug("VPC lookup")
        ec2 = boto3.client("ec2")
        search = ec2.describe_vpcs(Filters=filters)
        if len(search["Vpcs"]) == 1:
            vpc = search["Vpcs"][0]
            response_status = cfnresponse.SUCCESS
            cfnresponse.send(event, context, response_status, vpc, vpc["VpcId"])
        else:
            cfnresponse.send(event, context, response_status, response_data)

    elif event["ResourceType"] == "Custom::R53HostedZone":
        log.debug("R53 Hosted Zone lookup")
        r53 = boto3.client("route53")
        if "HostedZoneId" in filters_raw:
            zone_id = filters_raw["HostedZoneId"]
            zone = r53.get_hosted_zone(Id=zone_id)
        else:
            log.erro("Unsupported R53 filters")
            zone = False
        if zone:
            response_status = cfnresponse.SUCCESS
            cfnresponse.send(
                event, context, response_status, flat_out_dict(zone), zone_id
            )
        else:
            cfnresponse.send(event, context, response_status, response_data)

    else:
        log.error("Unsupported resource lookup")
        cfnresponse.send(event, context, response_status, response_data)
