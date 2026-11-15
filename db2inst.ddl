-- This CLP file was created using DB2LOOK Version "12.1" 
-- Timestamp: Sun Nov 15 12:23:44 2026
-- Database Name: DBCDW          
-- Database Manager Version: DB2/LINUXX8664 Version 12.1.5.0
-- Database Codepage: 1208
-- Database Collating Sequence is: IDENTITY
-- Alternate collating sequence(alt_collate): null
-- varchar2 compatibility(varchar2_compat): OFF


CONNECT TO DBCDW;

------------------------------------------------
-- DDL Statements for Schemas
------------------------------------------------

-- Running the DDL below will explicitly create a schema in the
-- new database that corresponds to an implicitly created schema
-- in the original database.

CREATE SCHEMA "DB2INST1";


---------------------------------
-- DDL Statements for Sequences
---------------------------------


CREATE SEQUENCE "DB2INST1"."SAMPSEQUENCE" AS BIGINT
	MINVALUE 1 MAXVALUE 9223372036854775807
	START WITH 1 INCREMENT BY 1
	CACHE 20 NO CYCLE NO ORDER;



------------------------------------------------
-- DDL Statements for Table "DB2INST1"."CL_SCHED"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."CL_SCHED"  (
		  "CLASS_CODE" CHAR(7 OCTETS) , 
		  "DAY" SMALLINT , 
		  "STARTING" TIME , 
		  "ENDING" TIME )   
		 DISTRIBUTE BY HASH("CLASS_CODE")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."DEPARTMENT"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."DEPARTMENT"  (
		  "DEPTNO" CHAR(3 OCTETS) NOT NULL , 
		  "DEPTNAME" VARCHAR(36 OCTETS) NOT NULL , 
		  "MGRNO" CHAR(6 OCTETS) , 
		  "ADMRDEPT" CHAR(3 OCTETS) NOT NULL , 
		  "LOCATION" CHAR(16 OCTETS) )   
		 DISTRIBUTE BY HASH("DEPTNO")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."DEPARTMENT"

ALTER TABLE "DB2INST1"."DEPARTMENT" 
	ADD CONSTRAINT "PK_DEPARTMENT" PRIMARY KEY
		("DEPTNO")
	ENFORCED;



-- DDL Statements for Indexes on Table "DB2INST1"."DEPARTMENT"

SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';

CREATE INDEX "DB2INST1"."XDEPT2" ON "DB2INST1"."DEPARTMENT" 
		("MGRNO" ASC)
		
		COMPRESS NO 
		INCLUDE NULL KEYS ALLOW REVERSE SCANS;

-- DDL Statements for Indexes on Table "DB2INST1"."DEPARTMENT"

SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';

CREATE INDEX "DB2INST1"."XDEPT3" ON "DB2INST1"."DEPARTMENT" 
		("ADMRDEPT" ASC)
		
		COMPRESS NO 
		INCLUDE NULL KEYS ALLOW REVERSE SCANS;
-- DDL Statements for Aliases based on Table "DB2INST1"."DEPARTMENT"

CREATE ALIAS "DB2INST1"."DEPT" FOR TABLE "DB2INST1"."DEPARTMENT";


------------------------------------------------
-- DDL Statements for Table "DB2INST1"."EMPLOYEE"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."EMPLOYEE"  (
		  "EMPNO" CHAR(6 OCTETS) NOT NULL , 
		  "FIRSTNME" VARCHAR(12 OCTETS) NOT NULL , 
		  "MIDINIT" CHAR(1 OCTETS) , 
		  "LASTNAME" VARCHAR(15 OCTETS) NOT NULL , 
		  "WORKDEPT" CHAR(3 OCTETS) , 
		  "PHONENO" CHAR(4 OCTETS) , 
		  "HIREDATE" DATE , 
		  "JOB" CHAR(8 OCTETS) , 
		  "EDLEVEL" SMALLINT NOT NULL , 
		  "SEX" CHAR(1 OCTETS) , 
		  "BIRTHDATE" DATE , 
		  "SALARY" DECIMAL(9,2) , 
		  "BONUS" DECIMAL(9,2) , 
		  "COMM" DECIMAL(9,2) )   
		 DISTRIBUTE BY HASH("EMPNO")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."EMPLOYEE"

ALTER TABLE "DB2INST1"."EMPLOYEE" 
	ADD CONSTRAINT "PK_EMPLOYEE" PRIMARY KEY
		("EMPNO")
	ENFORCED;



-- DDL Statements for Indexes on Table "DB2INST1"."EMPLOYEE"

SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';

CREATE INDEX "DB2INST1"."XEMP2" ON "DB2INST1"."EMPLOYEE" 
		("WORKDEPT" ASC)
		
		COMPRESS NO 
		INCLUDE NULL KEYS ALLOW REVERSE SCANS;
-- DDL Statements for Aliases based on Table "DB2INST1"."EMPLOYEE"

CREATE ALIAS "DB2INST1"."EMP" FOR TABLE "DB2INST1"."EMPLOYEE";


------------------------------------------------
-- DDL Statements for Table "DB2INST1"."EMP_PHOTO"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."EMP_PHOTO"  (
		  "EMPNO" CHAR(6 OCTETS) NOT NULL , 
		  "PHOTO_FORMAT" VARCHAR(10 OCTETS) NOT NULL , 
		  "PICTURE" BLOB(102400) LOGGED NOT COMPACT )   
		 DISTRIBUTE BY HASH("EMPNO",  
		 "PHOTO_FORMAT")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."EMP_PHOTO"

ALTER TABLE "DB2INST1"."EMP_PHOTO" 
	ADD CONSTRAINT "PK_EMP_PHOTO" PRIMARY KEY
		("EMPNO",
		 "PHOTO_FORMAT")
	ENFORCED;



------------------------------------------------
-- DDL Statements for Table "DB2INST1"."EMP_RESUME"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."EMP_RESUME"  (
		  "EMPNO" CHAR(6 OCTETS) NOT NULL , 
		  "RESUME_FORMAT" VARCHAR(10 OCTETS) NOT NULL , 
		  "RESUME" CLOB(5120 OCTETS) LOGGED NOT COMPACT )   
		 DISTRIBUTE BY HASH("EMPNO",  
		 "RESUME_FORMAT")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."EMP_RESUME"

ALTER TABLE "DB2INST1"."EMP_RESUME" 
	ADD CONSTRAINT "PK_EMP_RESUME" PRIMARY KEY
		("EMPNO",
		 "RESUME_FORMAT")
	ENFORCED;



------------------------------------------------
-- DDL Statements for Table "DB2INST1"."PROJECT"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."PROJECT"  (
		  "PROJNO" CHAR(6 OCTETS) NOT NULL , 
		  "PROJNAME" VARCHAR(24 OCTETS) NOT NULL WITH DEFAULT '' , 
		  "DEPTNO" CHAR(3 OCTETS) NOT NULL , 
		  "RESPEMP" CHAR(6 OCTETS) NOT NULL , 
		  "PRSTAFF" DECIMAL(5,2) , 
		  "PRSTDATE" DATE , 
		  "PRENDATE" DATE , 
		  "MAJPROJ" CHAR(6 OCTETS) )   
		 DISTRIBUTE BY HASH("PROJNO")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."PROJECT"

ALTER TABLE "DB2INST1"."PROJECT" 
	ADD CONSTRAINT "PK_PROJECT" PRIMARY KEY
		("PROJNO")
	ENFORCED;



-- DDL Statements for Indexes on Table "DB2INST1"."PROJECT"

SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';

CREATE INDEX "DB2INST1"."XPROJ2" ON "DB2INST1"."PROJECT" 
		("RESPEMP" ASC)
		
		COMPRESS NO 
		INCLUDE NULL KEYS ALLOW REVERSE SCANS;
-- DDL Statements for Aliases based on Table "DB2INST1"."PROJECT"

CREATE ALIAS "DB2INST1"."PROJ" FOR TABLE "DB2INST1"."PROJECT";


------------------------------------------------
-- DDL Statements for Table "DB2INST1"."PROJACT"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."PROJACT"  (
		  "PROJNO" CHAR(6 OCTETS) NOT NULL , 
		  "ACTNO" SMALLINT NOT NULL , 
		  "ACSTAFF" DECIMAL(5,2) , 
		  "ACSTDATE" DATE NOT NULL , 
		  "ACENDATE" DATE )   
		 DISTRIBUTE BY HASH("PROJNO",  
		 "ACTNO",  
		 "ACSTDATE")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."PROJACT"

ALTER TABLE "DB2INST1"."PROJACT" 
	ADD CONSTRAINT "PK_PROJACT" PRIMARY KEY
		("PROJNO",
		 "ACTNO",
		 "ACSTDATE")
	ENFORCED;



------------------------------------------------
-- DDL Statements for Table "DB2INST1"."EMPPROJACT"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."EMPPROJACT"  (
		  "EMPNO" CHAR(6 OCTETS) NOT NULL , 
		  "PROJNO" CHAR(6 OCTETS) NOT NULL , 
		  "ACTNO" SMALLINT NOT NULL , 
		  "EMPTIME" DECIMAL(5,2) , 
		  "EMSTDATE" DATE , 
		  "EMENDATE" DATE )   
		 DISTRIBUTE BY HASH("EMPNO")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 





-- DDL Statements for Aliases based on Table "DB2INST1"."EMPPROJACT"

CREATE ALIAS "DB2INST1"."EMPACT" FOR TABLE "DB2INST1"."EMPPROJACT";

CREATE ALIAS "DB2INST1"."EMP_ACT" FOR TABLE "DB2INST1"."EMPPROJACT";


------------------------------------------------
-- DDL Statements for Table "DB2INST1"."ACT"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."ACT"  (
		  "ACTNO" SMALLINT NOT NULL , 
		  "ACTKWD" CHAR(6 OCTETS) NOT NULL , 
		  "ACTDESC" VARCHAR(20 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("ACTNO")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."ACT"

ALTER TABLE "DB2INST1"."ACT" 
	ADD CONSTRAINT "PK_ACT" PRIMARY KEY
		("ACTNO")
	ENFORCED;



-- DDL Statements for Indexes on Table "DB2INST1"."ACT"

SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';

CREATE UNIQUE INDEX "DB2INST1"."XACT2" ON "DB2INST1"."ACT" 
		("ACTNO" ASC,
		 "ACTKWD" ASC)
		
		COMPRESS NO 
		INCLUDE NULL KEYS ALLOW REVERSE SCANS;

------------------------------------------------
-- DDL Statements for Table "DB2INST1"."IN_TRAY"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."IN_TRAY"  (
		  "RECEIVED" TIMESTAMP , 
		  "SOURCE" CHAR(8 OCTETS) , 
		  "SUBJECT" CHAR(64 OCTETS) , 
		  "NOTE_TEXT" VARCHAR(3000 OCTETS) )   
		 DISTRIBUTE BY HASH("RECEIVED")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."ORG"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."ORG"  (
		  "DEPTNUMB" SMALLINT NOT NULL , 
		  "DEPTNAME" VARCHAR(14 OCTETS) , 
		  "MANAGER" SMALLINT , 
		  "DIVISION" VARCHAR(10 OCTETS) , 
		  "LOCATION" VARCHAR(13 OCTETS) )   
		 DISTRIBUTE BY HASH("DEPTNUMB")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."STAFF"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."STAFF"  (
		  "ID" SMALLINT NOT NULL , 
		  "NAME" VARCHAR(9 OCTETS) , 
		  "DEPT" SMALLINT , 
		  "JOB" CHAR(5 OCTETS) , 
		  "YEARS" SMALLINT , 
		  "SALARY" DECIMAL(7,2) , 
		  "COMM" DECIMAL(7,2) )   
		 DISTRIBUTE BY HASH("ID")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."SALES"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."SALES"  (
		  "SALES_DATE" DATE , 
		  "SALES_PERSON" VARCHAR(15 OCTETS) , 
		  "REGION" VARCHAR(15 OCTETS) , 
		  "SALES" INTEGER )   
		 DISTRIBUTE BY HASH("SALES_DATE")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."STAFFG"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."STAFFG"  (
		  "ID" SMALLINT NOT NULL , 
		  "NAME" VARGRAPHIC(9 CODEUNITS16) , 
		  "DEPT" SMALLINT , 
		  "JOB" GRAPHIC(5 CODEUNITS16) , 
		  "YEARS" SMALLINT , 
		  "SALARY" DECIMAL(9,0) , 
		  "COMM" DECIMAL(9,0) )   
		 DISTRIBUTE BY HASH("ID")   
		   IN "USERSPACE1"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."ADEFUSR"
------------------------------------------------
 SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";

CREATE SUMMARY TABLE ADEFUSR AS (SELECT workdept, count(*) AS no_of_employees FROM employee GROUP BY workdept) DATA INITIALLY DEFERRED REFRESH IMMEDIATE ENABLE QUERY OPTIMIZATION MAINTAINED BY SYSTEM DISTRIBUTE BY HASH("WORKDEPT")  		  IN "USERSPACE1" 		ORGANIZE BY ROW;


ALTER TABLE "DB2INST1"."ADEFUSR" DEACTIVATE ROW ACCESS CONTROL;






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."EMPMDC"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."EMPMDC"  (
		  "EMPNO" INTEGER , 
		  "DEPT" INTEGER , 
		  "DIV" INTEGER )   
		 DISTRIBUTE BY HASH("EMPNO")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW USING ( 
		  ( "DEPT" ) , 
		  ( "DIV" ) ) 
		 ; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."DOCUMENTS_EUCLIDEAN"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."DOCUMENTS_EUCLIDEAN"  (
		  "ID" CHAR(16 OCTETS) NOT NULL , 
		  "TEXT" CLOB(1048576 OCTETS) LOGGED NOT COMPACT , 
		  "METADATA" BLOB(1048576) LOGGED NOT COMPACT , 
		  "EMBEDDING" VECTOR(768,FLOAT32) )   
		 DISTRIBUTE BY HASH("ID")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."DOCUMENTS_EUCLIDEAN"

ALTER TABLE "DB2INST1"."DOCUMENTS_EUCLIDEAN" 
	ADD PRIMARY KEY
		("ID")
	ENFORCED;



------------------------------------------------
-- DDL Statements for Table "DB2INST1"."TEST"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."TEST"  (
		  "EINS" VARCHAR(10 OCTETS) )   
		 DISTRIBUTE BY HASH("EINS")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."REGION"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."REGION"  (
		  "R_REGIONKEY" INTEGER NOT NULL , 
		  "R_NAME" CHAR(25 OCTETS) NOT NULL , 
		  "R_COMMENT" VARCHAR(152 OCTETS) )   
		 DISTRIBUTE BY HASH("R_REGIONKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."PART"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."PART"  (
		  "P_PARTKEY" INTEGER NOT NULL , 
		  "P_NAME" VARCHAR(55 OCTETS) NOT NULL , 
		  "P_MFGR" CHAR(25 OCTETS) NOT NULL , 
		  "P_BRAND" CHAR(10 OCTETS) NOT NULL , 
		  "P_TYPE" VARCHAR(25 OCTETS) NOT NULL , 
		  "P_SIZE" INTEGER NOT NULL , 
		  "P_CONTAINER" CHAR(10 OCTETS) NOT NULL , 
		  "P_RETAILPRICE" DECIMAL(15,2) NOT NULL , 
		  "P_COMMENT" VARCHAR(23 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("P_PARTKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."SUPPLIER"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."SUPPLIER"  (
		  "S_SUPPKEY" INTEGER NOT NULL , 
		  "S_NAME" CHAR(25 OCTETS) NOT NULL , 
		  "S_ADDRESS" VARCHAR(40 OCTETS) NOT NULL , 
		  "S_NATIONKEY" INTEGER NOT NULL , 
		  "S_PHONE" CHAR(15 OCTETS) NOT NULL , 
		  "S_ACCTBAL" DECIMAL(15,2) NOT NULL , 
		  "S_COMMENT" VARCHAR(101 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("S_SUPPKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."PARTSUPP"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."PARTSUPP"  (
		  "PS_PARTKEY" INTEGER NOT NULL , 
		  "PS_SUPPKEY" INTEGER NOT NULL , 
		  "PS_AVAILQTY" INTEGER NOT NULL , 
		  "PS_SUPPLYCOST" DECIMAL(15,2) NOT NULL , 
		  "PS_COMMENT" VARCHAR(199 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("PS_PARTKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."CUSTOMER"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."CUSTOMER"  (
		  "C_CUSTKEY" INTEGER NOT NULL , 
		  "C_NAME" VARCHAR(25 OCTETS) NOT NULL , 
		  "C_ADDRESS" VARCHAR(40 OCTETS) NOT NULL , 
		  "C_NATIONKEY" INTEGER NOT NULL , 
		  "C_PHONE" CHAR(15 OCTETS) NOT NULL , 
		  "C_ACCTBAL" DECIMAL(15,2) NOT NULL , 
		  "C_MKTSEGMENT" CHAR(10 OCTETS) NOT NULL , 
		  "C_COMMENT" VARCHAR(117 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("C_CUSTKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."ORDERS"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."ORDERS"  (
		  "O_ORDERKEY" INTEGER NOT NULL , 
		  "O_CUSTKEY" INTEGER NOT NULL , 
		  "O_ORDERSTATUS" CHAR(1 OCTETS) NOT NULL , 
		  "O_TOTALPRICE" DECIMAL(15,2) NOT NULL , 
		  "O_ORDERDATE" DATE NOT NULL , 
		  "O_ORDERPRIORITY" CHAR(15 OCTETS) NOT NULL , 
		  "O_CLERK" CHAR(15 OCTETS) NOT NULL , 
		  "O_SHIPPRIORITY" INTEGER NOT NULL , 
		  "O_COMMENT" VARCHAR(79 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("O_ORDERKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."LINEITEM"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."LINEITEM"  (
		  "L_ORDERKEY" INTEGER NOT NULL , 
		  "L_PARTKEY" INTEGER NOT NULL , 
		  "L_SUPPKEY" INTEGER NOT NULL , 
		  "L_LINENUMBER" INTEGER NOT NULL , 
		  "L_QUANTITY" DECIMAL(15,2) NOT NULL , 
		  "L_EXTENDEDPRICE" DECIMAL(15,2) NOT NULL , 
		  "L_DISCOUNT" DECIMAL(15,2) NOT NULL , 
		  "L_TAX" DECIMAL(15,2) NOT NULL , 
		  "L_RETURNFLAG" CHAR(1 OCTETS) NOT NULL , 
		  "L_LINESTATUS" CHAR(1 OCTETS) NOT NULL , 
		  "L_SHIPDATE" DATE NOT NULL , 
		  "L_COMMITDATE" DATE NOT NULL , 
		  "L_RECEIPTDATE" DATE NOT NULL , 
		  "L_SHIPINSTRUCT" CHAR(25 OCTETS) NOT NULL , 
		  "L_SHIPMODE" CHAR(10 OCTETS) NOT NULL , 
		  "L_COMMENT" VARCHAR(44 OCTETS) NOT NULL )   
		 DISTRIBUTE BY HASH("L_ORDERKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."NATION"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."NATION"  (
		  "N_NATIONKEY" INTEGER NOT NULL , 
		  "N_NAME" CHAR(25 OCTETS) NOT NULL , 
		  "N_REGIONKEY" INTEGER NOT NULL , 
		  "N_COMMENT" VARCHAR(152 OCTETS) )   
		 DISTRIBUTE BY HASH("N_NATIONKEY")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 






------------------------------------------------
-- DDL Statements for Table "DB2INST1"."DOCUMENT_CHUNKS_PDF"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."DOCUMENT_CHUNKS_PDF"  (
		  "CHUNK_ID" VARCHAR(64 OCTETS) NOT NULL , 
		  "DOC_ID" VARCHAR(128 OCTETS) , 
		  "SOURCE" VARCHAR(1024 OCTETS) , 
		  "PAGE_NUM" INTEGER , 
		  "CHUNK_INDEX" INTEGER , 
		  "CHUNK_TEXT" CLOB(2097152 OCTETS) LOGGED NOT COMPACT )   
		 DISTRIBUTE BY HASH("CHUNK_ID")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."DOCUMENT_CHUNKS_PDF"

ALTER TABLE "DB2INST1"."DOCUMENT_CHUNKS_PDF" 
	ADD PRIMARY KEY
		("CHUNK_ID")
	ENFORCED;



------------------------------------------------
-- DDL Statements for Table "DB2INST1"."DB2_INFO_CENTER"
------------------------------------------------
 

CREATE TABLE "DB2INST1"."DB2_INFO_CENTER"  (
		  "CHUNK_ID" VARCHAR(64 OCTETS) NOT NULL , 
		  "DOC_ID" VARCHAR(128 OCTETS) , 
		  "SOURCE" VARCHAR(1024 OCTETS) , 
		  "PAGE_NUM" INTEGER , 
		  "CHUNK_INDEX" INTEGER , 
		  "CHUNK_TEXT" CLOB(2097152 OCTETS) LOGGED NOT COMPACT )   
		 DISTRIBUTE BY HASH("CHUNK_ID")   
		   IN "IBMDB2SAMPLEREL"  
		 ORGANIZE BY ROW; 


-- DDL Statements for Primary Key on Table "DB2INST1"."DB2_INFO_CENTER"

ALTER TABLE "DB2INST1"."DB2_INFO_CENTER" 
	ADD PRIMARY KEY
		("CHUNK_ID")
	ENFORCED;



-- DDL Statements for Foreign Keys on Table "DB2INST1"."DEPARTMENT"

ALTER TABLE "DB2INST1"."DEPARTMENT" 
	ADD CONSTRAINT "RDE" FOREIGN KEY
		("MGRNO")
	REFERENCES "DB2INST1"."EMPLOYEE"
		("EMPNO")
	ON DELETE SET NULL
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

ALTER TABLE "DB2INST1"."DEPARTMENT" 
	ADD CONSTRAINT "ROD" FOREIGN KEY
		("ADMRDEPT")
	REFERENCES "DB2INST1"."DEPARTMENT"
		("DEPTNO")
	ON DELETE CASCADE
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."EMPLOYEE"

ALTER TABLE "DB2INST1"."EMPLOYEE" 
	ADD CONSTRAINT "RED" FOREIGN KEY
		("WORKDEPT")
	REFERENCES "DB2INST1"."DEPARTMENT"
		("DEPTNO")
	ON DELETE SET NULL
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Check Constraints on Table "DB2INST1"."EMPLOYEE"

SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';

ALTER TABLE "DB2INST1"."EMPLOYEE" 
	ADD CONSTRAINT "NUMBER" CHECK 
		(PHONENO >= '0000' AND PHONENO <= '9999')
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."EMP_PHOTO"

ALTER TABLE "DB2INST1"."EMP_PHOTO" 
	ADD CONSTRAINT "FK_EMP_PHOTO" FOREIGN KEY
		("EMPNO")
	REFERENCES "DB2INST1"."EMPLOYEE"
		("EMPNO")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."EMP_RESUME"

ALTER TABLE "DB2INST1"."EMP_RESUME" 
	ADD CONSTRAINT "FK_EMP_RESUME" FOREIGN KEY
		("EMPNO")
	REFERENCES "DB2INST1"."EMPLOYEE"
		("EMPNO")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."PROJECT"

ALTER TABLE "DB2INST1"."PROJECT" 
	ADD CONSTRAINT "FK_PROJECT_1" FOREIGN KEY
		("DEPTNO")
	REFERENCES "DB2INST1"."DEPARTMENT"
		("DEPTNO")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

ALTER TABLE "DB2INST1"."PROJECT" 
	ADD CONSTRAINT "FK_PROJECT_2" FOREIGN KEY
		("RESPEMP")
	REFERENCES "DB2INST1"."EMPLOYEE"
		("EMPNO")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

ALTER TABLE "DB2INST1"."PROJECT" 
	ADD CONSTRAINT "RPP" FOREIGN KEY
		("MAJPROJ")
	REFERENCES "DB2INST1"."PROJECT"
		("PROJNO")
	ON DELETE CASCADE
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."PROJACT"

ALTER TABLE "DB2INST1"."PROJACT" 
	ADD CONSTRAINT "RPAP" FOREIGN KEY
		("PROJNO")
	REFERENCES "DB2INST1"."PROJECT"
		("PROJNO")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."EMPPROJACT"

ALTER TABLE "DB2INST1"."EMPPROJACT" 
	ADD CONSTRAINT "REPAPA" FOREIGN KEY
		("PROJNO",
		 "ACTNO",
		 "EMSTDATE")
	REFERENCES "DB2INST1"."PROJACT"
		("PROJNO",
		 "ACTNO",
		 "ACSTDATE")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;

-- DDL Statements for Foreign Keys on Table "DB2INST1"."ACT"

ALTER TABLE "DB2INST1"."ACT" 
	ADD CONSTRAINT "RPAA" FOREIGN KEY
		("ACTNO")
	REFERENCES "DB2INST1"."ACT"
		("ACTNO")
	ON DELETE RESTRICT
	ON UPDATE NO ACTION
	ENFORCED
	ENABLE QUERY OPTIMIZATION;






---------------------------------
-- DDL Statements for User Defined Functions
---------------------------------


SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';
SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";

CREATE FUNCTION resign_employee (number CHAR(6))
  RETURNS TABLE (empno  CHAR(6),
                 salary DOUBLE,
                 dept   CHAR(3))
  MODIFIES SQL DATA
  LANGUAGE SQL
  BEGIN ATOMIC
-- -------------------------------------------------------------------------------------
-- Routine type:  SQL table function
-- Routine name:  resign_employee
--
-- Purpose:  This procedure takes in an employee number, then removes that
--           employee from the EMPLOYEE table.
--           A useful extension to this function would be to archive the
--           original record into an archive table.
--
-- --------------------------------------------------------------------------------------
    DECLARE l_salary DOUBLE;--
    DECLARE l_job CHAR(3);--

    SET (l_salary, l_job) = (SELECT salary, job
                               FROM OLD TABLE (DELETE FROM employee
                                                WHERE employee.empno = number));--

    RETURN VALUES (number,l_salary, l_job);--
  END
;


----------------------------

-- DDL Statements for Views

----------------------------
SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VDEPT      AS SELECT ALL DEPTNO,   DEPTNAME,   MGRNO,   ADMRDEPT
  FROM DEPT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VHDEPT    AS SELECT ALL DEPTNO ,   DEPTNAME,   MGRNO ,   ADMRDEPT,
  LOCATION   FROM DEPT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VEMP    AS SELECT ALL EMPNO ,   FIRSTNME,   MIDINIT ,   LASTNAME,
  WORKDEPT   FROM EMP;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VPROJ    AS SELECT ALL PROJNO, PROJNAME, DEPTNO, RESPEMP, PRSTAFF,
PRSTDATE, PRENDATE, MAJPROJ FROM PROJ;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VACT AS SELECT ALL ACTNO ,   ACTKWD ,   ACTDESC FROM ACT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VPROJACT    AS SELECT ALL PROJNO,ACTNO, ACSTAFF, ACSTDATE, ACENDATE
FROM PROJACT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VEMPPROJACT AS SELECT ALL EMPNO, PROJNO, ACTNO, EMPTIME, EMSTDATE,
EMENDATE FROM EMPPROJACT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VDEPMG1 (DEPTNO, DEPTNAME, MGRNO, FIRSTNME, MIDINIT,   LASTNAME,
ADMRDEPT) AS SELECT ALL DEPTNO, DEPTNAME, EMPNO, FIRSTNME, MIDINIT,   LASTNAME,
ADMRDEPT FROM DEPT LEFT OUTER  JOIN EMP ON MGRNO = EMPNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VEMPDPT1 (DEPTNO, DEPTNAME, EMPNO, FRSTINIT, MIDINIT,   LASTNAME,
WORKDEPT) AS SELECT ALL DEPTNO, DEPTNAME, EMPNO, SUBSTR(FIRSTNME, 1, 1),
MIDINIT,   LASTNAME, WORKDEPT FROM DEPT  RIGHT OUTER JOIN EMP ON WORKDEPT
= DEPTNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VASTRDE1   (DEPT1NO,DEPT1NAM,EMP1NO,EMP1FN,EMP1MI,EMP1LN,TYPE2,
  DEPT2NO,DEPT2NAM,EMP2NO,EMP2FN,EMP2MI,EMP2LN) AS SELECT ALL   D1.DEPTNO,D1.DEPTNAME,D1.MGRNO,D1.FIRSTNME,D1.MIDINIT,
  D1.LASTNAME, '1',   D2.DEPTNO,D2.DEPTNAME,D2.MGRNO,D2.FIRSTNME,D2.MIDINIT,
  D2.LASTNAME FROM VDEPMG1 D1, VDEPMG1 D2 WHERE D1.DEPTNO = D2.ADMRDEPT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VASTRDE2   (DEPT1NO,DEPT1NAM,EMP1NO,EMP1FN,EMP1MI,EMP1LN,TYPE2,
  DEPT2NO,DEPT2NAM,EMP2NO,EMP2FN,EMP2MI,EMP2LN) AS SELECT ALL   D1.DEPTNO,D1.DEPTNAME,D1.MGRNO,D1.FIRSTNME,D1.MIDINIT,
  D1.LASTNAME,'2',   D1.DEPTNO,D1.DEPTNAME,E2.EMPNO,E2.FIRSTNME,E2.MIDINIT,
  E2.LASTNAME FROM VDEPMG1 D1, EMP E2 WHERE D1.DEPTNO = E2.WORKDEPT;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VPROJRE1   (PROJNO,PROJNAME,PROJDEP,RESPEMP,FIRSTNME,MIDINIT,
  LASTNAME,MAJPROJ) AS SELECT ALL   PROJNO,PROJNAME,DEPTNO,EMPNO,FIRSTNME,MIDINIT,
  LASTNAME,MAJPROJ FROM PROJ, EMP WHERE RESPEMP = EMPNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VPSTRDE1   (PROJ1NO,PROJ1NAME,RESP1NO,RESP1FN,RESP1MI,RESP1LN,
  PROJ2NO,PROJ2NAME,RESP2NO,RESP2FN,RESP2MI,RESP2LN) AS SELECT ALL   P1.PROJNO,P1.PROJNAME,P1.RESPEMP,P1.FIRSTNME,P1.MIDINIT,
  P1.LASTNAME,   P2.PROJNO,P2.PROJNAME,P2.RESPEMP,P2.FIRSTNME,P2.MIDINIT,
  P2.LASTNAME FROM VPROJRE1 P1,   VPROJRE1 P2 WHERE P1.PROJNO = P2.MAJPROJ;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VPSTRDE2   (PROJ1NO,PROJ1NAME,RESP1NO,RESP1FN,RESP1MI,RESP1LN,
  PROJ2NO,PROJ2NAME,RESP2NO,RESP2FN,RESP2MI,RESP2LN) AS SELECT ALL   P1.PROJNO,P1.PROJNAME,P1.RESPEMP,P1.FIRSTNME,P1.MIDINIT,
  P1.LASTNAME,   P1.PROJNO,P1.PROJNAME,P1.RESPEMP,P1.FIRSTNME,P1.MIDINIT,
  P1.LASTNAME FROM VPROJRE1 P1 WHERE NOT EXISTS (SELECT * FROM VPROJRE1
P2 WHERE P1.PROJNO = P2.MAJPROJ);


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VFORPLA   (PROJNO,PROJNAME,RESPEMP,PROJDEP,FRSTINIT,MIDINIT,LASTNAME)
AS SELECT ALL F1.PROJNO,PROJNAME,RESPEMP,PROJDEP, SUBSTR(FIRSTNME, 1, 1),
  MIDINIT, LASTNAME FROM VPROJRE1 F1 LEFT OUTER JOIN EMPPROJACT F2 ON F1.PROJNO
= F2.PROJNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VSTAFAC1(PROJNO, ACTNO, ACTDESC, EMPNO, FIRSTNME, MIDINIT, 
    LASTNAME, EMPTIME,STDATE,ENDATE, TYPE) AS SELECT ALL PA.PROJNO, PA.ACTNO,
AC.ACTDESC,' ', ' ', ' ', ' ',   PA.ACSTAFF, PA.ACSTDATE,   PA.ACENDATE,'1'
FROM PROJACT PA, ACT AC  WHERE PA.ACTNO = AC.ACTNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VSTAFAC2 (PROJNO, ACTNO, ACTDESC, EMPNO, FIRSTNME, MIDINIT,
LASTNAME, EMPTIME,STDATE, ENDATE, TYPE) AS SELECT ALL EP.PROJNO, EP.ACTNO,
AC.ACTDESC, EP.EMPNO,EM.FIRSTNME, EM.MIDINIT, EM.LASTNAME, EP.EMPTIME,
EP.EMSTDATE,   EP.EMENDATE,'2' FROM EMPPROJACT EP, ACT AC, EMP EM WHERE
EP.ACTNO = AC.ACTNO AND EP.EMPNO = EM.EMPNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VPHONE   (LASTNAME,   FIRSTNAME,   MIDDLEINITIAL,   PHONENUMBER,
  EMPLOYEENUMBER,   DEPTNUMBER,   DEPTNAME) AS SELECT ALL LASTNAME,   FIRSTNME,
  MIDINIT ,   VALUE(PHONENO,' '),   EMPNO,   DEPTNO,   DEPTNAME FROM EMP,
DEPT WHERE WORKDEPT = DEPTNO;


SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE VIEW VEMPLP   (EMPLOYEENUMBER,   PHONENUMBER) AS SELECT ALL EMPNO
,   PHONENO FROM EMP;





---------------------------------
-- DDL Statements for Stored Procedures
---------------------------------


SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';
SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";

CREATE PROCEDURE bonus_increase                            (IN p_bonusFactor
DECIMAL (3,2),                              IN p_bonusMaxSumForDept DECIMAL
(9,2),                              OUT p_deptsWithoutNewBonuses VARCHAR(255),
                             OUT p_countDeptsViewed INTEGER,          
                   OUT p_countDeptsBonusChanged INTEGER,              
               OUT p_errorMsg VARCHAR(255)) SPECIFIC BONUS_INCREASE
LANGUAGE SQL
DYNAMIC RESULT SETS 1

BEGIN
-- -------------------------------------------------------------------------------------
-- Routine type:  SQL stored procedure
-- Routine name:  bonus_increase
--
-- Purpose:  This procedure takes in a multiplier value that is used to update
--           employee bonus values.  The employee bonus updates are done department
--           by department.  Updated employee bonus values are only committed if the
--           sum of the bonuses for a department does not exceed the threshold amount
--           specified by another input parameter.  A result is returned listing, by
--           department, employee numbers and currently set bonus values.
--
-- Features shown:
--           - IN and OUT parameters
--           - Variable declaration and setting
--           - Condition handler declaration and use
--           - Use of CURSOR WITH HOLD
--           - Use of SAVEPOINT and ROLLBACK to SAVEPOINT
--           - Returning of a result set to the caller
--           - Use of a WHILE loop control-statement
--           - Use of IF/ELSE statement
--           - Use of labels and GOTO statement
--           - Use of RETURN statement
--
-- Parameters:
-- IN  p_bonusFactor:      Constant multiple by which employee bonuses are updated
-- IN  p_bonusMaxSumForDept:    Maximum amount for departmental bonuses without review
-- OUT p_deptsWithoutNewBonuses:  Comma delimited list of departments that require
--                                   a manual setting and review of bonus amounts
-- OUT p_countDeptsViewed:     Number of departments processed
-- OUT p_countDeptsBonusChanged:  Number of departments for which bonuses were set
-- OUT p_errorMsg:       Error message string
-- --------------------------------------------------------------------------------------
    DECLARE v_dept, v_actdept CHAR(3);--
    DECLARE v_bonus, v_deptbonus, v_newbonus DECIMAL(9,2);--
    DECLARE v_empno CHAR(6);--
    DECLARE v_atend SMALLINT DEFAULT 0;--

    -- Cursor that lists employee numbers and bonuses ordered by department
    -- This cursor is declared as WITH HOLD so that on rollbacks it remains
    -- open.  It is declared as FOR UPDATE OF bonus, so that the employee
    -- bonus column field can be updated as the cursor iterates through the rows.

    DECLARE cSales CURSOR WITH HOLD FOR
          SELECT workdept, bonus, empno FROM employee ORDER BY workdept
      FOR UPDATE OF bonus;--

    -- This cursor, declared with WITH RETURN TO CALLER, is used to return
    -- a result set to the caller when this procedure returns.  The result
    -- set contains a list of the employees and their bonus values ordered
    -- by the department numbers.

    DECLARE cEmpBonuses CURSOR WITH RETURN TO CALLER FOR
          SELECT workdept, empno, bonus FROM employee ORDER BY workdept;--

    -- This continue handler is used to catch the NOT FOUND error
    -- associated with the end of the iteration over the cursor cSales.
    -- It is used to set v_atend which flags the end of the WHILE loop.

     DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_atend=1;--

    -- This continue handler is used to catch any numeric overflows

    DECLARE EXIT HANDLER FOR SQLSTATE '22003'
    BEGIN
      SET p_errorMsg = 'SQLSTATE 22003 - Numeric overflow occurred setting bonus';--
    END;--

    DECLARE EXIT HANDLER FOR SQLEXCEPTION SET v_atend=1;--

    -- Initialize local variables

    SET p_errorMsg = '';--
    SET p_deptsWithoutNewBonuses = '';--
    SET p_countDeptsViewed = 0;--
    SET p_countDeptsBonusChanged = 0;--

    -- Check input parameter is valid

    IF (p_bonusFactor < 1 OR p_bonusFactor > 2) THEN
      SET p_errorMsg = 'E01 Checking parameter p_bonusFactor, validation';--
      GOTO error_found;--
    END IF;--

    OPEN cSales;--

    FETCH cSales INTO v_dept, v_bonus, v_empno;--

    nextdept:
        IF v_atend = 0 THEN

            -- This savepoint is used to rollback the bonuses assigned to employees if
            -- the sum of bonuses for a department exceeds a threshold amount

            SAVEPOINT svpt_bonus ON ROLLBACK RETAIN CURSORS;--

            SET v_actdept = v_dept;--
            SET v_deptbonus = 0;--

            WHILE ( v_actdept = v_dept ) AND ( v_atend = 0 ) DO
                    SET v_newbonus = v_bonus * p_bonusFactor;--
                    UPDATE employee SET bonus = v_newbonus WHERE empno = v_empno;--
                    SET v_deptbonus = v_deptbonus + v_newbonus;--
                    FETCH cSales INTO v_dept, v_bonus, v_empno;--
            END WHILE;--

            SET p_countDeptsViewed = p_countDeptsViewed + 1;--

            IF v_deptbonus <= p_bonusMaxSumForDept THEN
                SET p_countDeptsBonusChanged = p_countDeptsBonusChanged + 1;--
                COMMIT;--
            ELSE
                     ROLLBACK TO SAVEPOINT svpt_bonus;--
                     RELEASE SAVEPOINT svpt_bonus;--
                     SET p_deptsWithoutNewBonuses =
                                     (CASE WHEN p_deptsWithoutNewBonuses = ''
                                           THEN v_actdept
                                      ELSE
                                           p_deptsWithoutNewBonuses || ', ' || v_actdept
                                      END);--
            END IF;--
            GOTO nextdept;--
        END IF;--

    OPEN cEmpBonuses;--

    RETURN 0;--

error_found:
    SET p_errorMsg = p_errorMsg || ' failed.';--
    RETURN -1;--

END;

-------------------------------
-- DDL Statements for Triggers
-------------------------------


SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';
SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE TRIGGER do_not_del_sales NO CASCADE BEFORE DELETE ON staff REFERENCING
OLD AS oldstaff FOR EACH ROW MODE DB2SQL WHEN(oldstaff.job = 'Sales') BEGIN
ATOMIC SIGNAL SQLSTATE '75000' ('Sales staff cannot be deleted... see the DO_NOT_DEL_SALES trigger.');
END;


SET SYSIBM.NLS_STRING_UNITS = 'SYSTEM';
SET CURRENT SCHEMA = "DB2INST1";
SET CURRENT PATH = "SYSIBM","SYSFUN","SYSPROC","SYSIBMADM","SYSHADOOP","DB2INST1";
CREATE TRIGGER min_salary NO CASCADE BEFORE INSERT ON staff REFERENCING
NEW AS newstaff FOR EACH ROW MODE DB2SQL BEGIN ATOMIC SET newstaff.salary
= CASE WHEN newstaff.job = 'Mgr' AND newstaff.salary < 17000.00 THEN 17000.00
WHEN newstaff.job = 'Sales' AND newstaff.salary < 14000.00 THEN 14000.00
WHEN newstaff.job = 'Clerk' AND newstaff.salary < 10000.00 THEN 10000.00
ELSE newstaff.salary END; END;


COMMIT WORK;

CONNECT RESET;

TERMINATE;

