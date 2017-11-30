SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for f in `find $1 -type f -iname '*.txt'`
do
    echo $f
    if file "$f" | grep --quiet 'Non-ISO extended-ASCII text'
    then
        echo windows
        iconv -f CP1252 -t UTF-8 "$f" > "$f".utf8
        mv "$f".utf8 "$f"
    fi
done
IFS=$SAVEIFS
