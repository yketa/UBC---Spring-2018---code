#! /bin/bash

# Letters expressions and floats conversion hash tables and conversion functions.

declare -A exponents # declares the hash table exponents
export exponents=(["a"]="-11" ["b"]="-10" ["c"]="-9" ["d"]="-8" ["e"]="-7" ["f"]="-6" ["g"]="-5" ["h"]="-4" ["i"]="-3" ["j"]="-2" ["k"]="-1" ["l"]="0" ["m"]="1" ["n"]="2" ["o"]="3" ["p"]="4" ["q"]="5" ["r"]="6" ["s"]="7" ["t"]="8" ["u"]="9" ["v"]="10" ["w"]="11" ["x"]="12" ["y"]="13" ["z"]="14") # hash table of the exponents

declare -A letters # declares the hash table letters
export letters=(["-11"]="a" ["-10"]="b" ["-09"]="c" ["-08"]="d" ["-07"]="e" ["-06"]="f" ["-05"]="g" ["-04"]="h" ["-03"]="i" ["-02"]="j" ["-01"]="k" ["+00"]="l" ["+01"]="m" ["+02"]="n" ["+03"]="o" ["+04"]="p" ["+05"]="q" ["+06"]="r" ["+07"]="s" ["+08"]="t" ["+09"]="u" ["+10"]="v" ["+11"]="w" ["+12"]="x" ["+13"]="y" ["+14"]="z") # hash table of the letters

letters_to_float () {
	# Returns the float associated to a letters expression.
	echo ${1:1:1}.${1:2:3}e${exponents[${1::1}]}
}
export -f letters_to_float

float_to_letters () {
	# Returns the letters expression associated to a float.
	float=`FLOAT=$1 /home/yketa/miniconda3/bin/python3.6 << 'EOF'
import os
print("%.3e" % float(eval(os.environ['FLOAT'])))
EOF
`
	echo ${letters[${float:6}]}${float:0:1}${float:2:3}
}
export -f float_to_letters

