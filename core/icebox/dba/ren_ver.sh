#! /bin/bash
#
# rename versions filename to 0001 , 0002, 0003, 0004 etc.
#
revs=$(alembic history | awk '{; print $3}' | tac)
cd versions
i=1
for rev in $revs
do
    rev=$(echo $rev | sed -r 's/,//g')
    newrev=$(printf '%04d' $i)
    echo $newrev
    rename 's/'$rev'/'$newrev'/' $rev_*.py

    i=$((i+1))
done

