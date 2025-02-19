import boto3
import csv
from botocore.exceptions import NoCredentialsError

def list_ec2_instance_types():
    ec2_client = boto3.client("ec2")
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
    
    with open("ec2_instance_types.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["region", "instance_type"])
        
        for region in regions:
            ec2_client = boto3.client("ec2", region_name=region)
            instance_types = set()
            
            try:
                response = ec2_client.describe_instance_type_offerings(LocationType='region', Filters=[{"Name": "location", "Values": [region]}])
                for instance in response['InstanceTypeOfferings']:
                    instance_types.add(instance['InstanceType'])
                
                for instance_type in instance_types:
                    writer.writerow([region, instance_type])
            except Exception as e:
                print(f"Error fetching instance types in {region}: {e}")

def list_billed_regions():
    ce_client = boto3.client("ce")
    response = ce_client.get_dimension_values(
        Dimension='REGION',
        TimePeriod={
            'Start': '2025-01-01', 
            'End': '2025-02-17'
        },
        Context='COST_AND_USAGE'
    )
    regions = [entry['Value'] for entry in response['DimensionValues']]
    print("Billed regions:", regions)


def check_mfa_for_users():
    iam_client = boto3.client("iam")
    users = iam_client.list_users()["Users"]
    
    with open("iam_users_mfa.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["IAMUserName", "MFAEnabled"])
        
        for user in users:
            mfa_devices = iam_client.list_mfa_devices(UserName=user["UserName"])['MFADevices']
            writer.writerow([user["UserName"], bool(mfa_devices)])

def check_public_sg():
    ec2_client = boto3.client("ec2")
    security_groups = ec2_client.describe_security_groups()["SecurityGroups"]
    
    with open("public_security_groups.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["SGName", "Port", "AllowedIP"])
        
        for sg in security_groups:
            for rule in sg["IpPermissions"]:
                for ip_range in rule.get("IpRanges", []):
                    if ip_range["CidrIp"] == "0.0.0.0/0":
                        writer.writerow([sg["GroupName"], rule.get("FromPort", "All"), ip_range["CidrIp"]])

def find_unused_ec2():
    cloudwatch = boto3.client("cloudwatch")
    ec2_client = boto3.client("ec2")
    instances = ec2_client.describe_instances()["Reservations"]
    
    for reservation in instances:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime='2024-01-01T00:00:00Z',
                EndTime='2024-12-31T23:59:59Z',
                Period=86400,
                Statistics=['Average']
            )
            
            avg_cpu = sum([datapoint["Average"] for datapoint in metrics.get("Datapoints", [])]) / (len(metrics.get("Datapoints", [])) or 1)
            if avg_cpu < 10:
                print(f"Instance {instance_id} has low CPU utilization.")

def find_idle_rds():
    rds_client = boto3.client("rds")
    instances = rds_client.describe_db_instances()["DBInstances"]
    
    for instance in instances:
        if instance["DBInstanceStatus"] == "available":
            print(f"RDS Instance {instance['DBInstanceIdentifier']} is running but might be idle.")

if __name__ == "__main__":
    list_ec2_instance_types()
    list_billed_regions()
    check_mfa_for_users()
    check_public_sg()
    find_unused_ec2()
    find_idle_rds()
