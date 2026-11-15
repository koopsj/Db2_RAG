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


COMMIT WORK;

CONNECT RESET;

TERMINATE;

