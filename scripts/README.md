#APM8 Scripts

## Goals
The scripts will do:
 1. Extract the IPM8 resources from APM8 environment (APM SaaS and APM on-prem) via API calls. The resources support Resource Groups,
 Agent and Threshold of now.
 
 2. Generate all the outputs to an XLS file;
 
 3. Support to work for multiple APM8 subscriptions and/or APM8 onprem, while the crenditals are configured;
 

## Prerequisites
Python3;

Run following command to install python modules:
```
sudo pip install --requirement requirement.txt
```
Tested on Linux.

## Usage
###1. Configure credentials in .json file
Create config/credential.json file based on config/credential.json.sample;

Valid value for "Type" is either "cloud" or "onprem"; for "Protocol" is either "http" or "https";

You can set "subsctiption" as any normal string which is easy to be remembered for your subscription or APM8 onprem;

You can add one or more indentical "subscription" with credentials into the .json file, but be sure the file applies standard json file format.

####For APM8 SaaS subscription:
if you have the pairs of Client_ID & Client_Secret, 
you can add the section likes "ipm8s1" subscription and fill all information into credential.json file;
Otherwise, you can add the section likes "ipm8s2" subscription and fill all information into credential.json file;

####For APM8 Onprem:
If APM8 env supports "http", you can add the section likes "ipm8p1", and change others to reflect to your environment;
If APM8 env supports "https", you can add the section likes "ipm8p2", and change others to reflect to your environment.
 

###2. Extract the resources from APM8
Run apm.py script to extract some or all resources ( supports Agents, ResourceGroups and Thresholds of now), and
store the output into a directory. E.g

```
$ ./apm.py  -s ipm8-1 -a returnAllAgents -o /tmp/ipm8-1
Running for ...: Return all agents
Successful, the information is gotten
The output file is:/tmp/ipm8-1/allAgents.json
```
You are able to do the same for "returnAllGroups", "returnAllThresholds" (and other in future).

###3. Generate reports
Run createJson2Xls.py to create reports based on the output of #2. E.g
```
$ ./createJson2Xls.py -d /tmp/ipm8-1
File of /tmp/ipm8-1/Monitoring_IPM8-20190219.xls is created.

```
###4. Create reports for other APM8 subscription or onprem, by repeating steps of 1-3
(with different subscription name, and different output directory)

## Constraints
1. Returns 401 error for APM8 onprem with "http" protocol for "returnAllThresholds", 
since port of 8090 was not officially supported in API calls.
