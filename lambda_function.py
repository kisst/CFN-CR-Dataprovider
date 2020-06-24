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

def flat_out_dict(d, flat=dict(), prefix=""):
    """ Flat out dict so all attributes can be accessed with GetAtt """
    for k,v in d.items():
        if prefix == "":
            key = str(k)
        else:
            key = prefix + "." + str(k)
        if isinstance(v, dict):
            flat_out_dict(v, flat, key)
        else:
            flat[key]=str(v)
    return(flat)

def handler(event, context):
    """Main Lambda Function"""
    response_data = {}

    log.debug("Received event: %s", json.dumps(event))
    try: filters = flat_out_filter(event["ResourceProperties"]["Filter"])
    except KeyError: filters = []
    log.debug("Where filters are: %s", filters)

    if event["RequestType"] == "Delete":
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
            cfnresponse.send(event, context, response_status, subnet, subnet["SubnetId"])
        else:
            response_status = cfnresponse.FAILED
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
            response_status = cfnresponse.FAILED
            cfnresponse.send(event, context, response_status, response_data)
    
    elif event["ResourceType"] == "Custom::R53HostedZone":
        log.debug("R53 Hosted Zone lookup")
        r53 = boto3.client("route53")
        try: zone_id = event["ResourceProperties"]["HostedZoneId"]
        except KeyError: zone_id = None
        zone = r53.get_hosted_zone(Id=zone_id)        
        if zone:
            response_status = cfnresponse.SUCCESS
            cfnresponse.send(event, context, response_status, flat_out_dict(zone), zone_id)
        else:
            response_status = cfnresponse.FAILED
            cfnresponse.send(event, context, response_status, response_data)

    else:
        log.error("Unsupported resource lookup")
        response_status = cfnresponse.FAILED
        cfnresponse.send(event, context, response_status, response_data)
