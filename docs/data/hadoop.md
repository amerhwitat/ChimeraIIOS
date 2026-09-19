# Apache Hadoop ecosystem integration

Chimera treats Hadoop as a distributed user-space data platform. The integration covers HDFS storage, YARN resource management, Hive SQL, HBase NoSQL, Spark and Tez execution, with optional Kafka, Ozone and Iceberg ecosystem components.

Hive provides SQL access to distributed data and can use different execution backends; version compatibility between Hive and Spark/other engines must be respected by the deployment. Configure cluster endpoints through environment variables or an external profile and keep Kerberos/TLS credentials outside the repository.

Use `tools/data/hadoop_doctor.py` for local client discovery. The doctor does not modify the cluster.
