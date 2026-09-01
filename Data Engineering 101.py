# Databricks notebook source
# DBTITLE 1,Project Documentation
# MAGIC %md
# MAGIC # Data Engineering 101 — Frasers Group Retail Database
# MAGIC
# MAGIC ## Project Overview
# MAGIC This notebook builds a relational retail database for **Frasers Group** in Databricks using Delta Lake tables within the `FRASERS_GROUP` schema. It covers the full data engineering lifecycle: schema creation, table design with primary and foreign keys, data ingestion, MERGE operations, analytical views, and sales fact-table population.
# MAGIC
# MAGIC ## Schema: FRASERS_GROUP
# MAGIC
# MAGIC ### Tables
# MAGIC
# MAGIC | Table | Type | Primary Key | Description |
# MAGIC | --- | --- | --- | --- |
# MAGIC | Products | Dimension | Product_code (STRING) | Product catalog with pricing, category, colour, and stock quantity |
# MAGIC | Customers | Dimension | Customer_id (BIGINT, IDENTITY) | Customer profiles with demographics, membership type, and status |
# MAGIC | Shops | Dimension | Shop_id (VARCHAR(20)) | Store locations across the UK with address and contact details |
# MAGIC | Staff | Dimension | Staff_id (BIGINT, IDENTITY) | Staff records with job title, salary, and shop assignment (FK → Shops) |
# MAGIC | Dim_sales | Fact | Sales_id (BIGINT, IDENTITY) | Sales transactions linking products, customers, staff, and shops |
# MAGIC | NewProducts | Staging | Product_code (STRING) | Staging table for MERGE upserts into Products |
# MAGIC
# MAGIC ### Foreign Key Relationships
# MAGIC
# MAGIC ```
# MAGIC Dim_sales ──→ Products   (Product_code)
# MAGIC Dim_sales ──→ Customers  (Customer_id)
# MAGIC Dim_sales ──→ Staff      (Staff_id)
# MAGIC Dim_sales ──→ Shops      (Shop_id)
# MAGIC Staff     ──→ Shops      (Shop_id)
# MAGIC ```
# MAGIC
# MAGIC ### Views
# MAGIC
# MAGIC | View | Description |
# MAGIC | --- | --- |
# MAGIC | vw_sales | Joins Dim_sales with all dimension tables to produce a denormalised sales report (customer name, product details, quantity, total amount, staff name, shop name) |
# MAGIC
# MAGIC ## Notebook Workflow
# MAGIC 1. **Schema setup** — Create the `FRASERS_GROUP` database
# MAGIC 2. **Products** — Create table, insert seed data, and view with revenue calculation
# MAGIC 3. **NewProducts staging** — Create staging table, insert data, and MERGE into Products (upsert + quantity accumulation)
# MAGIC 4. **Customers** — Create table with IDENTITY column, insert customer records, and query with age calculation
# MAGIC 5. **Shops** — Create table and insert 14 UK store locations
# MAGIC 6. **Staff** — Create table with FK to Shops, insert 40 staff records, and count staff per shop
# MAGIC 7. **Dim_sales** — Create fact table with FKs to all dimensions, insert 39 sales transactions
# MAGIC 8. **vw_sales** — Create analytical view joining fact and dimension tables
# MAGIC
# MAGIC ## Key Databricks Features Used
# MAGIC * Delta Lake tables with `USING DELTA`
# MAGIC * `GENERATED ALWAYS AS IDENTITY` for surrogate keys
# MAGIC * Primary key and foreign key constraints in Unity Catalog
# MAGIC * `MERGE INTO` for SCD-Type-1 upserts with quantity accumulation
# MAGIC * `TRUNCATE TABLE` for staging cleanup
# MAGIC * SQL views for denormalised reporting
# MAGIC * Date functions (`months_between`, `CURRENT_DATE`) for age calculation
# MAGIC * `ROUND`, `CONCAT`, `FLOOR` for data formatting
# MAGIC
# MAGIC ## Author
# MAGIC Daniel Arebu — Data Engineering 101 Project

# COMMAND ----------

# DBTITLE 1,Cell 1
# MAGIC %sql
# MAGIC CREATE DATABASE IF NOT EXISTS FRASERS_GROUP;

# COMMAND ----------

# DBTITLE 1,Cell 2
# MAGIC %sql
# MAGIC USE FRASERS_GROUP;

# COMMAND ----------

# DBTITLE 1,Cell 3
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS Products (
# MAGIC     Product_code STRING NOT NULL PRIMARY KEY,
# MAGIC     Product_name STRING NOT NULL,
# MAGIC     Product_description STRING NOT NULL,
# MAGIC     Product_category STRING NOT NULL,
# MAGIC     Product_price FLOAT NOT NULL,
# MAGIC     Product_colour STRING NOT NULL,
# MAGIC     Product_quantity INT NOT NULL
# MAGIC )
# MAGIC USING DELTA;
# MAGIC
# MAGIC INSERT INTO FRASERS_GROUP.Products (Product_code,Product_name,Product_description,Product_category,Product_price,Product_colour,Product_quantity)
# MAGIC VALUES
# MAGIC ('21567/23/454','Lipstick','Lipstick with a matte finish','Makeup','24.99','Pink',100),
# MAGIC ('21567/23/455','Lipstick','Lipstick with a glossy finish','Makeup','29.99','White',100),
# MAGIC ('21567/23/456','Lipstick','Lipstick with a satin finish','Makeup','24.99','Black',100),
# MAGIC ('21567/23/457','Lipstick','Lipstick with a sheer finish','Makeup','29.99','Green',100),
# MAGIC ('21567/23/458','Lipstick','Lipstick with a glossy finish','Makeup','29.99','Yellow',100),
# MAGIC ('21567/23/459','Lipstick','Lipstick with a matte finish','Makeup','24.99','Blue',100),
# MAGIC ('21567/23/460','Lipstick','Lipstick with a glossy finish','Makeup','29.99','Red',100);

# COMMAND ----------

# DBTITLE 1,Cell 4
# MAGIC %sql
# MAGIC SELECT 
# MAGIC         Product_code,
# MAGIC         Product_name,
# MAGIC         Product_description,
# MAGIC         Product_category,
# MAGIC         ROUND(Product_price) AS Price,
# MAGIC         Product_colour,
# MAGIC         Product_quantity,
# MAGIC         ROUND(Product_price * Product_quantity) AS Revenue
# MAGIC FROM FRASERS_GROUP.Products;

# COMMAND ----------

# DBTITLE 1,Cell 5
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS NewProducts (
# MAGIC     Product_code STRING NOT NULL PRIMARY KEY,
# MAGIC     Product_name STRING NOT NULL,
# MAGIC     Product_description STRING NOT NULL,
# MAGIC     Product_category STRING NOT NULL,
# MAGIC     Product_price FLOAT NOT NULL,
# MAGIC     Product_colour STRING NOT NULL,
# MAGIC     Product_quantity INT NOT NULL
# MAGIC )
# MAGIC USING DELTA;

# COMMAND ----------

# DBTITLE 1,Cell 6
# MAGIC %sql
# MAGIC INSERT INTO FRASERS_GROUP.NewProducts (Product_code,Product_name,Product_description,Product_category,Product_price,Product_colour,Product_quantity)
# MAGIC VALUES
# MAGIC ('21567/23/454','Lipstick','Lipstick with a matte finish','Makeup','24.99','Pink',50);

# COMMAND ----------

# DBTITLE 1,Cell 7
# MAGIC %sql
# MAGIC SELECT * from newproducts;

# COMMAND ----------

# DBTITLE 1,Cell 8
# MAGIC %sql
# MAGIC MERGE INTO Products AS target
# MAGIC USING NewProducts AS source
# MAGIC
# MAGIC ON target.Product_code = source.Product_code
# MAGIC
# MAGIC WHEN MATCHED THEN
# MAGIC     UPDATE SET
# MAGIC         target.Product_name = source.Product_name,
# MAGIC         target.Product_price = source.Product_price,
# MAGIC         target.Product_quantity = target.Product_quantity + source.Product_quantity
# MAGIC
# MAGIC WHEN NOT MATCHED THEN
# MAGIC     INSERT (
# MAGIC         Product_code,
# MAGIC         Product_name,
# MAGIC         Product_description,
# MAGIC         Product_category,
# MAGIC         Product_price,
# MAGIC         Product_colour,
# MAGIC         Product_quantity
# MAGIC     )
# MAGIC     VALUES (
# MAGIC         source.Product_code,
# MAGIC         source.Product_name,
# MAGIC         source.Product_description,
# MAGIC         source.Product_category,
# MAGIC         source.Product_price,
# MAGIC         source.Product_colour,
# MAGIC         source.Product_quantity
# MAGIC     );
# MAGIC
# MAGIC     TRUNCATE TABLE NewProducts;

# COMMAND ----------

# DBTITLE 1,Customers Table
# MAGIC %sql
# MAGIC CREATE TABLE Customers (
# MAGIC     Customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY NOT NULL,
# MAGIC     Customer_name STRING NOT NULL,
# MAGIC     Customer_Postal Varchar(15) NOT NULL,
# MAGIC     Customer_email STRING NOT NULL,
# MAGIC     Customer_phone BIGINT NOT NULL,
# MAGIC     Birth_date DATE NOT NULL,
# MAGIC     Customer_gender STRING NOT NULL,
# MAGIC     Membership_Type STRING NOT NULL,
# MAGIC     Status STRING NOT NULL 
# MAGIC )
# MAGIC USING DELTA;

# COMMAND ----------

# DBTITLE 1,Inserting Into Customers Table
# MAGIC %sql
# MAGIC INSERT INTO frasers_group.Customers (Customer_name,Customer_Postal,Customer_email,Customer_phone,Birth_date,Customer_gender,Membership_Type,Status)
# MAGIC VALUES 
# MAGIC ('Daniel Arebu','NG20TN','danielarebu@outlook.com','07767864861784','1990-01-01','Male','Premium','Active'),
# MAGIC ('Paul Mormon','MC20TN','paulmorgan@outlook.com','0776748244944','1993-01-01','Male','Standard','Active'),
# MAGIC ('Sarah Matthew','MC20TN','sarahmatthew@outlook.com','0776748244944','1993-01-01','Female','Standard','Active');

# COMMAND ----------

# DBTITLE 1,Formuarization
# MAGIC %sql
# MAGIC SELECT 
# MAGIC Customer_id ,
# MAGIC     Customer_name,
# MAGIC     Customer_Postal,
# MAGIC     Customer_email,
# MAGIC     Customer_phone,
# MAGIC     Birth_date,
# MAGIC     FLOOR(months_between(CURRENT_DATE(), Birth_date) / 12) AS Age,
# MAGIC     Customer_gender,
# MAGIC     Membership_Type,
# MAGIC     Status
# MAGIC FROM frasers_group.customers

# COMMAND ----------

# DBTITLE 1,Create Table for Shops
# MAGIC %sql
# MAGIC CREATE TABLE iF NOT EXISTS Shops (
# MAGIC     Shop_id VARCHAR(20) PRIMARY KEY NOT NULL,
# MAGIC     Shop_name STRING NOT NULL,
# MAGIC     Shop_address STRING NOT NULL,
# MAGIC     Shop_city STRING NOT NULL,
# MAGIC     Shop_state STRING NOT NULL,
# MAGIC     Shop_country STRING NOT NULL,
# MAGIC     Shop_postcode VARCHAR(15) NOT NULL,
# MAGIC     Shop_phone BIGINT NOT NULL,
# MAGIC     Shop_email VARCHAR(30) NOT NULL
# MAGIC )
# MAGIC USING DELTA;

# COMMAND ----------

# DBTITLE 1,Cell 13
# MAGIC %sql
# MAGIC SELECT * FROM frasers_group.shops;

# COMMAND ----------

# DBTITLE 1,Insert Into shops table
# MAGIC %sql
# MAGIC INSERT INTO frasers_group.shops(shop_id,Shop_name,Shop_address,Shop_city,Shop_state,Shop_country,Shop_postcode,Shop_phone,Shop_email)
# MAGIC VALUES 
# MAGIC ('SHL001','Shirebrook Vale Shop','11 Shire Brook Vale','Shirebrook','Derbyshire','England','NG21 7AT','04578',CONCAT('SHL001','@frasers.com')),
# MAGIC ('SHL002','Mansfield Central Shop','24 Market Place','Mansfield','Nottinghamshire','England','NG18 1HY','04579',CONCAT('SHL002','@frasers.com')),
# MAGIC ('SHL003','Nottingham City Shop','15 Victoria Centre','Nottingham','Nottinghamshire','England','NG1 3QN','04580',CONCAT('SHL003','@frasers.com')),
# MAGIC ('SHL004','Sheffield Meadowhall Shop','32 High Street','Sheffield','South Yorkshire','England','S9 1EP','04581',CONCAT('SHL004','@frasers.com')),
# MAGIC ('SHL005','Derby Intu Shop','18 Derby Road','Derby','Derbyshire','England','DE1 2JF','04582',CONCAT('SHL005','@frasers.com')),
# MAGIC ('SHL006','Leicester Highcross Shop','41 Highcross Street','Leicester','Leicestershire','England','LE1 4AN','04583',CONCAT('SHL006','@frasers.com')),
# MAGIC ('SHL007','Birmingham Bullring Shop','27 Bullring','Birmingham','West Midlands','England','B4 7SL','04584',CONCAT('SHL007','@frasers.com')),
# MAGIC ('SHL008','Leeds Trinity Shop','56 Albion Street','Leeds','West Yorkshire','England','LS1 5AT','04585',CONCAT('SHL008','@frasers.com')),
# MAGIC ('SHL009','Manchester Arndale Shop','73 Market Street','Manchester','Greater Manchester','England','M4 3AB','04586',CONCAT('SHL009','@frasers.com')),
# MAGIC ('SHL010','Liverpool One Shop','22 Paradise Street','Liverpool','Merseyside','England','L1 8JF','04587',CONCAT('SHL010','@frasers.com')),
# MAGIC ('SHL011','Sheffield City Shop','39 Fargate','Sheffield','South Yorkshire','England','S1 2HE','04588',CONCAT('SHL011','@frasers.com')),
# MAGIC ('SHL012','Nottingham Broadmarsh Shop','64 Carrington Street','Nottingham','Nottinghamshire','England','NG2 3AQ','04589',CONCAT('SHL012','@frasers.com')),
# MAGIC ('SHL013','Coventry City Shop','29 Broadgate','Coventry','West Midlands','England','CV1 1NF','04590',CONCAT('SHL013','@frasers.com')),
# MAGIC ('SHL014','Leicester Haymarket Shop','48 Haymarket','Leicester','Leicestershire','England','LE1 3GD','04591',CONCAT('SHL014','@frasers.com'));

# COMMAND ----------

# DBTITLE 1,Staff Table
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS Staff (
# MAGIC Staff_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY NOT NULL,
# MAGIC Shop_id VARCHAR(20) NOT NULL,
# MAGIC Staff_name STRING NOT NULL,
# MAGIC Email_address STRING NOT NULL,
# MAGIC Gender STRING NOT NULL,
# MAGIC Date_of_birth DATE NOT NULL,
# MAGIC Date_of_joining DATE NOT NULL,
# MAGIC Job_Title STRING NOT NULL,
# MAGIC Salary FLOAT NOT NULL,
# MAGIC Status STRING NOT NULL,
# MAGIC
# MAGIC FOREIGN KEY (Shop_id) REFERENCES Shops(Shop_id)
# MAGIC )
# MAGIC USING DELTA;

# COMMAND ----------

# DBTITLE 1,Cell 16
# MAGIC %sql
# MAGIC INSERT INTO Staff
# MAGIC (Shop_id, Staff_name, Email_address, Gender, Date_of_birth, Date_of_joining, Job_Title, Salary, Status)
# MAGIC VALUES
# MAGIC
# MAGIC ('SHL007','Emily Carter','emily.carter@frasers.com','Female','1997-09-22','2023-02-18','Sales Assistant',24500,'Active'),
# MAGIC ('SHL014','Jack Johnson','jack.johnson@frasers.com','Male','1989-08-21','2019-02-10','Store Manager',44000,'Active'),
# MAGIC ('SHL003','Grace Taylor','grace.taylor@frasers.com','Female','1996-12-10','2022-09-11','Sales Assistant',24500,'Active'),
# MAGIC ('SHL019','Theo Reed','theo.reed@frasers.com','Male','1994-11-20','2021-05-17','Assistant Manager',35000,'Active'),
# MAGIC ('SHL001','James Wilson','james.wilson@frasers.com','Male','1992-04-15','2021-06-12','Store Manager',42000,'Active'),
# MAGIC ('SHL011','Evie Adams','evie.adams@frasers.com','Female','1998-10-05','2023-08-28','Sales Assistant',24500,'Active'),
# MAGIC ('SHL004','Amelia Evans','amelia.evans@frasers.com','Female','1998-06-25','2023-07-03','Customer Service Advisor',25500,'Active'),
# MAGIC ('SHL018','Muhammad Morris','muhammad.morris@frasers.com','Male','1986-01-31','2018-09-24','Store Manager',45500,'Active'),
# MAGIC ('SHL009','Jacob Green','jacob.green@frasers.com','Male','1994-06-16','2021-01-18','Assistant Manager',36000,'Active'),
# MAGIC ('SHL015','Freya Parker','freya.parker@frasers.com','Female','1998-02-19','2023-10-02','Sales Assistant',24500,'Active'),
# MAGIC ('SHL002','Daniel Thompson','daniel.thompson@frasers.com','Male','1988-11-03','2019-08-20','Store Manager',43500,'Active'),
# MAGIC ('SHL020','Phoebe Bell','phoebe.bell@frasers.com','Female','1998-11-27','2023-05-22','Sales Assistant',24500,'Active'),
# MAGIC ('SHL006','Jessica Lewis','jessica.lewis@frasers.com','Female','1995-05-30','2022-06-27','Sales Assistant',25000,'Active'),
# MAGIC ('SHL013','Henry Campbell','henry.campbell@frasers.com','Male','1991-09-29','2021-03-22','Assistant Manager',35000,'Active'),
# MAGIC ('SHL008','Thomas Wright','thomas.wright@frasers.com','Male','1986-09-07','2017-08-21','Store Manager',47000,'Active'),
# MAGIC ('SHL017','Sienna Sanchez','sienna.sanchez@frasers.com','Female','1999-05-06','2024-06-10','Sales Assistant',24000,'Active'),
# MAGIC ('SHL005','George Thomas','george.thomas@frasers.com','Male','1993-10-08','2021-11-22','Assistant Manager',35000,'Active'),
# MAGIC ('SHL012','Ruby Mitchell','ruby.mitchell@frasers.com','Female','1997-04-23','2022-02-14','Sales Assistant',25000,'Active'),
# MAGIC ('SHL010','William King','william.king@frasers.com','Male','1985-12-02','2016-04-11','Store Manager',48000,'Active'),
# MAGIC ('SHL016','Leo Collins','leo.collins@frasers.com','Male','1988-04-07','2019-12-09','Store Manager',42500,'Active'),
# MAGIC ('SHL003','Oliver Brown','oliver.brown@frasers.com','Male','1991-07-28','2020-04-06','Assistant Manager',34000,'Active'),
# MAGIC ('SHL010','Mia Scott','mia.scott@frasers.com','Female','2001-07-13','2024-05-20','Sales Assistant',23800,'Active'),
# MAGIC ('SHL001','Emily Carter2','emily.carter2@frasers.com','Female','1995-03-12','2022-11-14','Customer Service Advisor',26000,'Active'),
# MAGIC ('SHL016','Florence Edwards','florence.edwards@frasers.com','Female','1996-07-21','2022-05-23','Sales Assistant',25000,'Active'),
# MAGIC ('SHL006','Jack Wilson','jack.wilson@frasers.com','Male','1990-05-18','2020-08-17','Assistant Manager',35500,'Active'),
# MAGIC ('SHL020','Freddie Morgan','freddie.morgan@frasers.com','Male','1989-07-09','2019-10-28','Store Manager',43500,'Active'),
# MAGIC ('SHL013','Florence Anderson','florence.anderson@frasers.com','Female','1995-12-16','2020-07-06','Customer Service Advisor',26000,'Active'),
# MAGIC ('SHL007','Charlie Walker','charlie.walker@frasers.com','Male','1990-01-12','2020-10-05','Assistant Manager',35500,'Active'),
# MAGIC ('SHL018','Isabelle Rogers','isabelle.rogers@frasers.com','Female','1997-03-15','2023-01-09','Customer Service Advisor',25500,'Active'),
# MAGIC ('SHL004','Harry Davies','harry.davies@frasers.com','Male','1987-03-19','2018-05-14','Store Manager',45000,'Active'),
# MAGIC ('SHL009','Lily Allen','lily.allen@frasers.com','Female','1996-08-09','2022-11-07','Customer Service Advisor',26000,'Active'),
# MAGIC ('SHL012','Alfie Nelson','alfie.nelson@frasers.com','Male','1989-05-11','2019-06-03','Store Manager',43000,'Active'),
# MAGIC ('SHL005','Isla Roberts','isla.roberts@frasers.com','Female','2000-02-14','2024-03-19','Sales Assistant',24000,'Active'),
# MAGIC ('SHL017','Arthur Stewart','arthur.stewart@frasers.com','Male','1990-10-13','2020-02-17','Assistant Manager',35500,'Active'),
# MAGIC ('SHL002','Sophie Williams','sophie.williams@frasers.com','Female','1999-01-17','2024-01-15','Sales Assistant',24000,'Active'),
# MAGIC ('SHL014','Oscar Carter','oscar.carter@frasers.com','Male','1987-06-04','2018-11-19','Store Manager',44500,'Active'),
# MAGIC ('SHL008','Poppy Hall','poppy.hall@frasers.com','Female','1999-03-26','2024-02-12','Sales Assistant',24000,'Active'),
# MAGIC ('SHL015','Archie Turner','archie.turner@frasers.com','Male','1993-01-25','2021-08-16','Assistant Manager',34500,'Active'),
# MAGIC ('SHL011','Noah Baker','noah.baker@frasers.com','Male','1992-02-27','2020-09-14','Assistant Manager',34500,'Active'),
# MAGIC ('SHL019','Matilda Cook','matilda.cook@frasers.com','Female','2000-12-03','2024-07-15','Sales Assistant',24000,'Active');

# COMMAND ----------

# DBTITLE 1,Cell 17
# MAGIC %sql
# MAGIC SELECT  Shop_name, COUNT(Staff_name) AS staff_number FROM Staff
# MAGIC JOIN Shops ON Staff.Shop_id = Shops.Shop_id
# MAGIC GROUP BY Shop_name;

# COMMAND ----------

# DBTITLE 1,Cell 18
# MAGIC %sql
# MAGIC INSERT INTO Dim_sales (
# MAGIC     Sales_Date,
# MAGIC     Product_code,
# MAGIC     Quantity,
# MAGIC     Customer_id,
# MAGIC     Staff_id,
# MAGIC     Shop_id
# MAGIC )
# MAGIC VALUES
# MAGIC
# MAGIC ('2026-01-05 09:15:00', '21567/23/454', 2, 1, 1, 'SHL007'),
# MAGIC ('2026-01-05 10:42:00', '21567/23/455', 1, 2, 2, 'SHL014'),
# MAGIC ('2026-01-06 12:18:00', '21567/23/456', 3, 3, 3, 'SHL003'),
# MAGIC ('2026-01-07 14:35:00', '21567/23/457', 1, 1, 5, 'SHL001'),
# MAGIC ('2026-01-08 16:22:00', '21567/23/458', 2, 2, 6, 'SHL011'),
# MAGIC ('2026-01-10 11:05:00', '21567/23/459', 4, 3, 7, 'SHL004'),
# MAGIC ('2026-01-12 13:47:00', '21567/23/460', 1, 1, 9, 'SHL009'),
# MAGIC ('2026-01-14 15:30:00', '21567/23/454', 2, 2, 11, 'SHL002'),
# MAGIC ('2026-01-15 17:12:00', '21567/23/455', 1, 3, 13, 'SHL006'),
# MAGIC ('2026-01-17 10:25:00', '21567/23/456', 3, 1, 14, 'SHL013'),
# MAGIC ('2026-01-18 12:40:00', '21567/23/457', 1, 2, 15, 'SHL008'),
# MAGIC ('2026-01-20 14:10:00', '21567/23/458', 2, 3, 17, 'SHL005'),
# MAGIC ('2026-01-22 09:55:00', '21567/23/459', 5, 1, 18, 'SHL012'),
# MAGIC ('2026-01-24 16:45:00', '21567/23/460', 2, 2, 19, 'SHL010'),
# MAGIC ('2026-01-25 18:20:00', '21567/23/454', 1, 3, 21, 'SHL003'),
# MAGIC ('2026-01-27 11:35:00', '21567/23/455', 2, 1, 22, 'SHL010'),
# MAGIC ('2026-01-28 13:05:00', '21567/23/456', 3, 2, 23, 'SHL001'),
# MAGIC ('2026-01-29 15:55:00', '21567/23/457', 1, 3, 25, 'SHL006'),
# MAGIC ('2026-01-30 10:15:00', '21567/23/458', 2, 1, 27, 'SHL013'),
# MAGIC ('2026-01-31 17:40:00', '21567/23/459', 4, 2, 28, 'SHL007'),
# MAGIC ('2026-02-02 09:20:00', '21567/23/460', 2, 3, 30, 'SHL004'),
# MAGIC ('2026-02-03 11:45:00', '21567/23/454', 3, 1, 31, 'SHL009'),
# MAGIC ('2026-02-05 13:10:00', '21567/23/455', 1, 2, 32, 'SHL012'),
# MAGIC ('2026-02-06 15:25:00', '21567/23/456', 2, 3, 33, 'SHL005'),
# MAGIC ('2026-02-08 16:50:00', '21567/23/457', 4, 1, 35, 'SHL002'),
# MAGIC ('2026-02-10 10:35:00', '21567/23/458', 1, 2, 36, 'SHL014'),
# MAGIC ('2026-02-12 12:15:00', '21567/23/459', 3, 3, 37, 'SHL008'),
# MAGIC ('2026-02-14 14:40:00', '21567/23/460', 2, 1, 39, 'SHL011'),
# MAGIC ('2026-02-16 09:05:00', '21567/23/454', 1, 2, 1, 'SHL007'),
# MAGIC ('2026-02-18 10:30:00', '21567/23/455', 2, 3, 2, 'SHL014'),
# MAGIC ('2026-02-20 12:55:00', '21567/23/456', 1, 1, 3, 'SHL003'),
# MAGIC ('2026-02-21 15:20:00', '21567/23/457', 3, 2, 5, 'SHL001'),
# MAGIC ('2026-02-23 17:05:00', '21567/23/458', 2, 3, 6, 'SHL011'),
# MAGIC ('2026-02-25 11:15:00', '21567/23/459', 4, 1, 7, 'SHL004'),
# MAGIC ('2026-02-26 13:40:00', '21567/23/460', 1, 2, 9, 'SHL009'),
# MAGIC ('2026-02-27 16:10:00', '21567/23/454', 2, 3, 11, 'SHL002'),
# MAGIC ('2026-02-28 10:45:00', '21567/23/455', 3, 1, 13, 'SHL006'),
# MAGIC ('2026-03-01 14:25:00', '21567/23/456', 1, 2, 14, 'SHL013');

# COMMAND ----------

# DBTITLE 1,Sales Table
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS Dim_sales (
# MAGIC     Sales_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
# MAGIC     Sales_Date TIMESTAMP,
# MAGIC     Product_code STRING,
# MAGIC     Quantity INT,
# MAGIC     Customer_id BIGINT,
# MAGIC     Staff_id BIGINT,
# MAGIC     Shop_id VARCHAR(20),
# MAGIC     FOREIGN KEY (Product_code) REFERENCES FRASERS_GROUP.Products(Product_code),
# MAGIC     FOREIGN KEY (Customer_id) REFERENCES FRASERS_GROUP.Customers(Customer_id),
# MAGIC     FOREIGN KEY (Staff_id) REFERENCES FRASERS_GROUP.Staff(Staff_id),
# MAGIC     FOREIGN KEY (Shop_id) REFERENCES FRASERS_GROUP.Shops(Shop_id)
# MAGIC )
# MAGIC USING DELTA;

# COMMAND ----------

# DBTITLE 1,Cell 20
# MAGIC %sql
# MAGIC CREATE VIEW vw_sales AS 
# MAGIC SELECT
# MAGIC         s.sales_id,
# MAGIC         s.Sales_Date,
# MAGIC         c.Customer_name,
# MAGIC         p.Product_code,
# MAGIC         p.Product_description,
# MAGIC         s.Quantity,
# MAGIC         ROUND(s.Quantity * p.Product_price,2) AS Total_Amount,
# MAGIC         st.Staff_name,
# MAGIC         sh.Shop_name
# MAGIC FROM Dim_sales s
# MAGIC INNER JOIN FRASERS_GROUP.Products p ON s.Product_code = p.Product_code
# MAGIC JOIN FRASERS_GROUP.Customers c ON s.Customer_id = c.Customer_id
# MAGIC JOIN FRASERS_GROUP.Staff st ON s.Staff_id = st.Staff_id
# MAGIC JOIN FRASERS_GROUP.Shops sh ON s.Shop_id = sh.Shop_id;

# COMMAND ----------

# DBTITLE 1,vW_Sales
# MAGIC %sql
# MAGIC SELECT * FROM vw_sales;

# COMMAND ----------

# DBTITLE 1,Cell 22
# MAGIC %sql
# MAGIC DROP TABLE Dim_sales;

# COMMAND ----------

