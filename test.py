import boto3
import json
ec2_client=boto3.client('ec2')
print('My instances')
response = ec2_client.describe_instances()
#print(json.dumps(response, indent=4, default=str)) 
for i in response['Reservations']:
    for j in i['Instances']:
        print(j['InstanceId'],j['InstanceType'],j['LaunchTime'])