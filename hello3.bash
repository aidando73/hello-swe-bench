
echo $1

cd /Users/aidand/dev/hello-swe-bench/django

./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1