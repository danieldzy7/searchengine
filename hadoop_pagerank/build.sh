if [ ! -d classes ]; then
        mkdir classes;
fi

# Compile WordCount
javac -classpath $HADOOP_HOME/hadoop-core-0.20.203.0.jar:$HADOOP_HOME/lib/commons-cli-1.2.jar -d ./classes WordCount.java

# Create the Jar
jar -cvf wordcount.jar -C ./classes/ .
 
# Copy the jar file to the Hadoop distributions
cp wordcount.jar $HADOOP_HOME/bin/ 

