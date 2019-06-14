import json
import os
import logging
import re
import boto3
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    
    # TODO implement
    logger.info("ALF - here should be the tagging of the new snapshot")
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)

    # https://docs.aws.amazon.com/server-migration-service/latest/userguide/cwe-sms.html
    # https://docs.aws.amazon.com/lambda/latest/dg/python-logging.html
    if 'snapshot_id' in event['detail']:
        
        region = event['region']
        result = event['detail']['result']
        snapshotArn = event['detail']['snapshot_id']
        volumeArn = event['detail']['source']
    
        logger.info(region)
        logger.info(result)
        logger.info(snapshotArn)
        logger.info(volumeArn)
        
        
        # create an ec2 client
        ec2 = boto3.client('ec2', region_name=region)
        ecs = boto3.client('ecs', region_name=region)
        
        snapshotId=''
        try:
            snapshotId = re.search('.*/(snap-.+)', snapshotArn).group(1)
        except AttributeError:
            logger.error("Could not retrieve the snapshot id from snapshot arn: "+snapshotArn)
            exit(1)
        logger.info(snapshotId)
        
        volumeId=''
        try:
            volumeId = re.search('.*/(vol-.+)', volumeArn).group(1)
        except AttributeError:
            logger.error("Could not retrieve the volume id from volume arn: "+volumeArn)
            exit(1)
        logger.info(volumeId)
    

        # get the attachement infos
        try:
            attachement = ec2.describe_volumes(
                VolumeIds=[
                    volumeId
                ]
            )['Volumes'][0]['Attachments'][0]
            logger.info(attachement)
        except:
            logger.error("Could not retrieve the volume attachement for volume: "+volumeId)
            exit(1)
        
        # find the matching instance from attachement
        attachEc2InstanceId=attachement['InstanceId']
        attachDevice=attachement['Device']
        logger.info(attachEc2InstanceId)
        logger.info(attachDevice)
        
        
        #logger.info(result)
        ecsCluster=""
        ecsContainerInstanceId=""
        rc = ecs.list_clusters()
        for cluster in rc['clusterArns']:
            ci = ecs.list_container_instances(cluster=cluster, filter="ec2InstanceId in ['{}']".format(attachEc2InstanceId))
        
            if len(ci['containerInstanceArns']) > 0:
                ecsContainerInstanceId=ci['containerInstanceArns'][0]
                ecsCluster=cluster
                
        logger.info(ecsCluster)
        logger.info(ecsContainerInstanceId)
        if not ecsContainerInstanceId:
            logger.error("Could not find the containerInstanceId in ECS clusters for ec2 instance: "+attachEc2InstanceId)
            exit(1)


        # get the tasks on the containerInstance: names, ids
        taskArns = ecs.list_tasks(
            cluster=ecsCluster,
            containerInstance=ecsContainerInstanceId
        )['taskArns']
        logger.info(taskArns)
        
        if not len(taskArns) > 0:
            logger.info("No tasks are scheduled to the instance {} by cluster {}".format(attachEc2InstanceId,ecsCluster))
            return
        
        # get the task details
        tasks=ecs.describe_tasks(
            cluster=ecsCluster,
            tasks=taskArns
        )['tasks']
        logger.info(tasks)
        
        taskContainers={}
        for task in tasks:
            taskDefinitionArn=task['taskDefinitionArn']
            taskDefinition=ecs.describe_task_definition(
                taskDefinition=taskDefinitionArn
            )['taskDefinition']
            logger.info(taskDefinition)

            
            for containerDefinition in taskDefinition['containerDefinitions']:
                # get container name
                containerName=containerDefinition['name']

                # get container labels    
                dockerLabels=containerDefinition['dockerLabels']
                logger.info(dockerLabels)
                taskContainers[containerName]=dockerLabels

        logger.info(taskContainers)

        tags=[]        
        for taskContainerName in taskContainers:
            labels=taskContainers[taskContainerName]
            logger.info("Adding labels for container {} : {}".format(taskContainerName,labels))
            
            tags.append({'Key': taskContainerName, 'Value': 'true'})
            
            for labelKey in labels:
                tags.append({'Key': "ecs_{}_{}".format(taskContainerName, labelKey), 'Value': labels[labelKey]})





        # tag the volume by the task names
        logger.info("Will add following tags to the snapshot {}: {}".format(snapshotArn,tags))
        ec2.create_tags(
            Resources=[
                snapshotId,
            ],
            Tags=tags
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Alf Hello from Lambda!')
    }
