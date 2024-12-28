


cd /Users/aidand/dev/hello-swe-bench/django

echo "Running command: ./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 $1"

./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 $1