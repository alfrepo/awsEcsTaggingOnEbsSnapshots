#!/bin/bash
set -e # stop on error

# change to the script folder 
cd "$(dirname "$0")"
scriptdir="$(pwd)"


builddir="$scriptdir/build"
mkdir -p $builddir

zipsrcpath="$builddir/function.zip"

# get the lambda zip
if [ ! -f $zipsrcpath ];
then
  echo "$zipsrcpath not exists"
  cd ../python/
  zip $zipsrcpath function.py
  cd -
else
    echo "$zipsrcpath exists"
fi



# the accounts, where the pipeline will run.
# The profiles should be already declared in .aws here
declare -a arr=("dev" "devops" "stage" "prod" "demo")

## now loop through the above accounts and deploy the roles
for i in "${arr[@]}"
do
    export AWS_PROFILE=${i}

    echo -e "\n\n---\n$AWS_PROFILE"

    my_s3_bucket="pla-arc-$AWS_PROFILE-cfpackagebucket"
    myStackName="tag-arc-$AWS_PROFILE-ecstagging"
    s3prefix="$myStackName"
    temporaryfile="/tmp/temporary_template.yml"
    template="../cloudformation/_lambdaEcsTagging_root.yml"
    my_s3_lambda_key="${myStackName}/function.zip"

    myPlatformPrefix="pla-arc-$AWS_PROFILE-infraplatform"

    # upload the lambda zip
    aws s3 cp $zipsrcpath s3://${my_s3_bucket}/${myStackName}/

    # deploy
    aws cloudformation package \
    --template-file $template \
    --s3-bucket $my_s3_bucket \
    --s3-prefix $s3prefix \
    --force-upload \
    --output-template-file $temporaryfile


    aws cloudformation deploy \
    --template-file $temporaryfile \
    --stack-name $myStackName  \
    --parameter-overrides TargetAwsAccount=${AWS_PROFILE} \
    LambdaZipS3path="s3://${my_s3_bucket}/${my_s3_lambda_key}" \
    ExportPrefix=${myStackName} \
    PlatformPrefix=${myPlatformPrefix} \
    LambdaS3Bucket=${my_s3_bucket} \
    LambdaS3Key=${my_s3_lambda_key} \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

done
