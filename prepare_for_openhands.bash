# cd /Users/aidand/dev/hello-swe-bench
# zip -r django.zip django/ -x "django/env/*" "django/test.patch"

echo "Copying django to OpenHands workspace"

cp -r django/ /Users/aidand/dev/OpenHands/workspace/django
trash /Users/aidand/dev/OpenHands/workspace/django/env
trash /Users/aidand/dev/OpenHands/workspace/django/test.patch
trash /Users/aidand/dev/OpenHands/workspace/django/django/gold.patch

echo -e "\033[32mDone\033[0m"