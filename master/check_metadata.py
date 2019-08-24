# Copyright 2010-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This file is licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License. A copy of the
# License is located at
#
# http://aws.amazon.com/apache2.0/
#
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
# 
# This script is used to validate metadata in the awsdocs/aws-doc-sdk-examples/ repository on Github.
# 

import os, fnmatch, sys, re

def checkFile(filePattern):
    filepath = ""
    filecount = 0
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, filePattern):
            # Ignore this file
            if filename == sys.argv[0]:
                continue
            if filename in doNotScan:
                if not quiet:
                    print("\nFile: " + filepath + ' is skipped')
                continue
            wordcount = 0
            filecount += 1
            errors = []
            filepath = os.path.join(path, filename)
            if not quiet:
                print("\nChecking File: " + filepath)
            with open(filepath) as f:
                s = f.read()
                
                #Check for Deny List words in file
                verifyNoDenyListWords(s, filepath)
                
                #Check for SecretKeys
                characterScan(s, filepath)
                fileNameCheck(filename, filepath)
                
                # Split file into list of strings separated by space
                words = s.split()
            for word in words:
                wordcount +=1

            # Check for mismatched Snippet start and end.    
            snippets = s.split('snippet-')

            # Check Metadata for optional metadata
            errors.append(snippetStartCheck(words, filepath))
            errors.append(snippetAuthorCheck(snippets))
            errors.append(snippetServiceCheck(snippets))
            errors.append(snippetDescriptionCheck(snippets))
            errors.append(snippetTypeCheck(snippets))
            errors.append(snippetDateCheck(snippets))
            errors.append(snippetKeywordCheck(snippets))
            f.close()
            if not quiet:
                print(str(wordcount) + " words found.")
            if warn:
                # Filter to only warning messages
                errors = list(filter(None, errors))
                # print out file name, if warnings found
                if len(errors) > 0 and quiet == True:
                    print("\nChecking File: " + filepath)
                for error in errors:
                    if error:
                        print(error)
    print(str(filecount) + " files scanned in " + root)
    print("")


def verifyNoDenyListWords(fileContents, filelocation):
    fileContents = fileContents.split('/')
    for word in fileContents:
        if word in denyList:
            print("ERROR -- Found in " + filelocation)
            sys.exit("ERROR -- " + word + " found, and is not allowed.")

def characterScan(fileContents, filelocation):
    twenty = re.findall("[^A-Z0-9][A][ACGIKNPRS][A-Z]{2}[A-Z0-9]{16}[^A-Z0-9]", fileContents)
    if (twenty) :
        for word in twenty:
            if word[1:-1] in allowList:
                continue
            print("ERROR -- " + word[1:-1] + " Found in " + filelocation)
            sys.exit("ERROR -- 20 character string found, and might be a secret access key.") 
    forty = re.findall("[^a-zA-Z0-9/+=][a-zA-Z0-9/+=]{40}[^a-zA-Z0-9/+=]", fileContents)
    if (forty) :
        for word in forty:
            if word[1:-1] in allowList:
                continue
            print("ERROR -- " + word[1:-1] + " Found in " + filelocation)
            sys.exit("ERROR -- 40 character string found, and might be a secret key.") 
            
def fileNameCheck(filename, filelocation):
    forty = re.findall("[^a-zA-Z0-9/+=][a-zA-Z0-9/+=]{40}[^a-zA-Z0-9/+=]", filename)
    if (forty) :
        if forty[0][-1] not in allowList:
           print("ERROR -- " + forty[0][:-1] + " Found in " + filelocation)
           sys.exit("ERROR -- Filename is 40 characters long, and should be renamed or added to allow list.")

def snippetStartCheck(words, filelocation):
    #print (words)
    snippetStart = 'snippet-start:['
    snippetEnd = 'snippet-end:['
    snippetTags = set()
    for s in words:
        if snippetStart in s:
            s = s.split('[')[1]
            snippetTags.add(s)
        elif snippetEnd in s:
            s = s.split('[')[1]
            if s in snippetTags:
                snippetTags.remove(s)
            else:
                print("ERROR -- Found in " + filelocation)
                sys.exit("ERROR -- " + s + "'s matching start tag not found.") 
        
    if len(snippetTags) > 0 : 
        print("ERROR -- Found in " + filelocation)
        print(snippetTags)
        sys.exit("ERROR -- " + snippetTags.pop() + "'s matching end tag not found.")

def snippetAuthorCheck(words):
    author = 'sourceauthor:['
    matching = [s for s in words if author in s]
    if not matching:
        if warn:
            return "WARNING -- Missing snippet-sourceauthor:[Your Name]"

def snippetServiceCheck(words):
    service = 'service:['
    matching = [s for s in words if service in s]
    if not matching:
        if warn:
            return "WARNING -- Missing snippet-service:[AWS service name] \nFind a list of AWS service names under AWS Service Namespaces in the General Reference Guide: https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html"

def snippetDescriptionCheck(words):
    desc = 'sourcedescription:['
    matching = [s for s in words if desc in s]
    if not matching:
        if warn:
            return "WARNING -- Missing snippet-sourcedescription:[Filename demonstrates how to ... ]"

def snippetTypeCheck(words):
    author = 'sourcetype:['
    matching = [s for s in words if author in s]
    containsType = False
    if not matching:
        containsType = False
    for match in matching:
        if match.startswith('sourcetype:[full-example'):
            containsType = True
            break
        elif match.startswith('sourcetype:[snippet'):
            containsType = True
            break
    if not containsType:
        if warn:
            return "WARNING -- Missing snippet-sourcetype:[full-example] or snippet-sourcetype:[snippet]"
        

def snippetDateCheck(words):
    datetag = 'sourcedate:['
    matching = [s for s in words if datetag in s]
    if not matching:
        if warn:
            return "WARNING -- Missing snippet-sourcedate:[YYYY-MM-DD]"

def snippetKeywordCheck(words):
    snippetkeyword = 'keyword:['
    matching = [s for s in words if snippetkeyword in s]
    # print(matching)
    codeSample = [s for s in words if 'keyword:[Code Sample]\n' in s]
    if not codeSample:
        if warn:
            return "WARNING -- Missing snippet-keyword:[Code Sample]"
    keywordServiceName(matching)
    keywordLanguageCheck(matching)
    keywordSDKCheck(matching)

def keywordServiceName(words):
    containsServiceTag = False
    AWS = 'keyword:[AWS'
    matching = [s for s in words if AWS in s]
    if matching:
        containsServiceTag = True
    Amazon = 'keyword:[Amazon'
    matching = [s for s in words if Amazon in s]
    if matching:
        containsServiceTag = True
    if not containsServiceTag:
        if warn:
            return "WARNING -- Missing snippet-keyword:[FULL SERVICE NAME]"

def keywordLanguageCheck(words):
    languages = ['C++', 'C', '.NET', 'Go', 'Java', 'JavaScript', 'PHP', 'Python', 'Ruby','TypeScript' ]
    containsLanguageTag = False
    for language in languages:
        languagekeyword = [s for s in words if 'keyword:[' + language + ']' in s]
        if languagekeyword:
            containsLanguageTag = True
            break
    if not containsLanguageTag:
        if warn:
            return "WARNING -- Missing snippet-keyword:[Language] \nOptions include:" + ', '.join(languages)
            

def keywordSDKCheck(words):
    sdkVersions = ['AWS SDK for PHP v3', 'AWS SDK for Python (Boto3)', 'CDK V0.14.1' ]
    containsSDKTag = False
    for sdk in sdkVersions:
        sdkkeyword = [s for s in words if 'keyword:[' + sdk + ']']
        if sdkkeyword:
            containsSDKTag = True
            break
    if not containsSDKTag:
        if warn:
            return "WARNING -- Missing snippet-keyword:[SDK Version used] \nOptions include:" + ', '.join(sdkVersions)

# We allow two args:
#     -w to suppress warnings
#     -q to suppress name of file we are parsing (quiet mode)
warn = True
quiet = False

i = 0

while i < len(sys.argv):
    if sys.argv[i] == "-w":
        warn = False
    elif sys.argv[i] == "-q":
        quiet = True
    i += 1

# Whitelist of files to never check
# 
doNotScan = {'AssemblyInfo.cs', 'CMakeLists.txt', 'check_metadata.py', 'movie_data.json'}
root = './'

# list of words that should not in include in code samples

denyList = {'alpha-docs-aws.amazon.com', 'integ-docs-aws.amazon.com'}
allowList = {
    'AKIAIOSFODNN7EXAMPLE',
    'AppStreamUsageReportsCFNGlueAthenaAccess',
    'aws/cloudtrail/model/LookupEventsRequest',
    'aws/codebuild/model/BatchGetBuildsResult',
    'aws/codecommit/model/DeleteBranchRequest',
    'aws/codecommit/model/ListBranchesRequest',
    'aws/dynamodb/model/ProvisionedThroughput',
    'aws/ec2/model/CreateSecurityGroupRequest',
    'aws/ec2/model/DeleteSecurityGroupRequest',
    'aws/ec2/model/UnmonitorInstancesResponse',
    'aws/email/model/CreateReceiptRuleRequest',
    'aws/email/model/DeleteReceiptRuleRequest',
    'aws/email/model/ListReceiptFiltersResult',
    'aws/email/model/SendTemplatedEmailResult',
    'aws/guardduty/model/ListDetectorsRequest',
    'aws/iam/model/GetAccessKeyLastUsedResult',
    'aws/iam/model/GetServerCertificateResult',
    'aws/kinesis/model/GetShardIteratorResult',
    'aws/kinesis/model/PutRecordsRequestEntry',
    'aws/monitoring/model/DeleteAlarmsRequest',
    'aws/neptune/model/CreateDBClusterRequest',
    'aws/neptune/model/DeleteDBClusterRequest',
    'aws/neptune/model/ModifyDBClusterRequest',
    'CertificateTransparencyLoggingPreference',
    'ChangeMessageVisibilityBatchRequestEntry',
    'com/greengrass/latest/developerguide/lra',
    'com/greengrass/latest/developerguide/sns',
    'com/samples/JobStatusNotificationsSample',
    'generate_presigned_url_and_upload_object',
    'KinesisStreamSourceConfiguration=kinesis',
    'nFindProductsWithNegativePriceWithConfig',
    's3_client_side_encryption_sym_master_key',
    'serial/CORE_THING_NAME/write/dev/serial1',
    'TargetTrackingScalingPolicyConfiguration',
    'targetTrackingScalingPolicyConfiguration',
    'upload_files_using_managed_file_uploader',
    'videoMetaData=celebrityRecognitionResult',
    'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
}

print ('----------\n\nRun Tests\n')

print ('----------\n\nC Code Examples (*.c)\n')
checkFile('*.c')
print ('----------\n\nCloudFormation and IAM Policy Code Examples (*.json) & (*.yaml)\n')
checkFile('*.json')
checkFile('*.yml')
checkFile('*.yaml')
print ('----------\n\nC++ Code Examples (*.cpp)\n')
checkFile('*.cpp')
print ('----------\n\nC# Code Examples (*.cs)\n')
checkFile('*.cs')
# checkFile( './', '*.txt', warn, quiet, doNotScan)
print ('----------\n\nGo Code Examples (*.go)\n')
checkFile('*.go')
print ('----------\n\nJava Code Examples (*.java)\n')
checkFile('*.java')
print ('----------\n\nJavaScript Code Examples (*.js)\n')
checkFile('*.js')
checkFile('*.html')
print ('----------\n\nPHP Code Examples (*.php)\n')
checkFile('*.php')
print ('----------\n\nPython Code Examples (*.py)\n')
checkFile('*.py')
print ('----------\n\nRuby Code Examples (*.rb)\n')
checkFile('*.rb')
print ('----------\n\nTypeScript Code Examples (*.ts)\n')
checkFile('*.ts')
