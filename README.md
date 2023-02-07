# odiolosaudios
Serverless lambda in AWS to create a Telegram bot to transcribe audios

## How to get it running...

### Before all, check the settings

You should take a look at the settings in serverless.yml, keep in mind that it's designed for my needs, not necessarily yours. For instance, see if the AWS region suits you.

Then, take a look at the Python handler, you'll see that it's designed to allow only the users in **permitidos**. I did that to prevent unexpected bills from AWS. You should change this to include your username or whoever you like. You could also remove that control by removing the **@check_permitido** decorator.

### First, create a bot in Telegram

To do so, you could take a look at the official documentation at https://core.telegram.org/bots , there are hundreds of sites that explain how to do that.

The result of the previous step should be a **TELEGRAM_TOKEN** that we'll use in the near future.

### Fetch dependencies

In the same directory where you have the files, type:

```
pip install -r requirements.txt
```

### Set environment variables

Then, you would need to add three environment variables: **TELEGRAM_TOKEN, AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY**. The first one is the token you got in the first step and the least two are your key and secret from your AWS account. If you are running this in Linux, this should look like:

```
export TELEGRAM_TOKEN=ddghhgdyhgd:7867d86d786d756d7857d8567d
export AWS_ACCESS_KEY_ID=suhsusghuyfddvhdguydguydguydguy
export AWS_SECRET_ACCESS_KEY=suyghsduysghuysghuysgysgysgsygsygsysgysgysgsygsygsygs
```

### Deploy the lambda

Next step is to deploy the lambda:

```
sls deploy
```

If everything worked fine, this should return an URL in the form:

https://XXXXX.execute-api.YOURREGION.amazonaws.com/pro/odiolosaudios

### Setting the webhook

The last step is setting the webhook of the Telegram bot. To do so, you'd only have to make a POST call to the URL:

https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook

with the payload:

```
{"url": "https://XXXXX.execute-api.YOURREGION.amazonaws.com/pro/odiolosaudios"}
```

If you are running this on Linux, you could use CURL to do that:

```
curl --request POST --url https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook --header 'content-type: application/json' --data '{"url": "https://XXXXX.execute-api.YOURREGION.amazonaws.com/pro/odiolosaudios"}'
```
