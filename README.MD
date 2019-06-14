Creates the IAM roles security groups and a lambda, which taggs an EBS snapshot with the docker-labels from the ECS clusters containers if the ec2 instance to which the volume is attached - is part of the ECS cluser. <br>
The deployed lambda will be started, when a new snapshot is created. <br>
The lambda will add the docker label tags to the new snapshot. <br>


How to run:

Replace the imports in the cloudformation scripts and in shell/_tool_deploy.sh by your own AWS ressources.
run shell/_tool_deploy.sh

