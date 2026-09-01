# Database Schema — FRASERS_GROUP

This document provides the complete schema definition for all tables and views in the `FRASERS_GROUP` database.

---

## 1. Products (Dimension Table)

```sql
CREATE TABLE IF NOT EXISTS Products (
    Product_code STRING NOT NULL PRIMARY KEY,
    Product_name STRING NOT NULL,
    Product_description STRING NOT NULL,
    Product_category STRING NOT NULL,
    Product_price FLOAT NOT NULL,
    Product_colour STRING NOT NULL,
    Product_quantity INT NOT NULL
)
USING DELTA;
```

- **Primary Key:** `Product_code` (natural key, format: `21567/23/454`)
- **Rows:** 7 product records (lipsticks with different finishes and colours)
- **Constraint:** PK registered as `products_pk` in Unity Catalog

---

## 2. NewProducts (Staging Table)

```sql
CREATE TABLE IF NOT EXISTS NewProducts (
    Product_code STRING NOT NULL PRIMARY KEY,
    Product_name STRING NOT NULL,
    Product_description STRING NOT NULL,
    Product_category STRING NOT NULL,
    Product_price FLOAT NOT NULL,
    Product_colour STRING NOT NULL,
    Product_quantity INT NOT NULL
)
USING DELTA;
```

- **Primary Key:** `Product_code`
- **Purpose:** Staging table for MERGE upserts into `Products`
- **Lifecycle:** Truncated after each MERGE operation

---

## 3. Customers (Dimension Table)

```sql
CREATE TABLE Customers (
    Customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY NOT NULL,
    Customer_name STRING NOT NULL,
    Customer_Postal VARCHAR(15) NOT NULL,
    Customer_email STRING NOT NULL,
    Customer_phone BIGINT NOT NULL,
    Birth_date DATE NOT NULL,
    Customer_gender STRING NOT NULL,
    Membership_Type STRING NOT NULL,
    Status STRING NOT NULL
)
USING DELTA;
```

- **Primary Key:** `Customer_id` (surrogate key, auto-incremented starting at 1)
- **Rows:** 3 customer records
- **Constraint:** PK registered as `customers_pk` in Unity Catalog
- **Identity:** `GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1)`

---

## 4. Shops (Dimension Table)

```sql
CREATE TABLE IF NOT EXISTS Shops (
    Shop_id VARCHAR(20) PRIMARY KEY NOT NULL,
    Shop_name STRING NOT NULL,
    Shop_address STRING NOT NULL,
    Shop_city STRING NOT NULL,
    Shop_state STRING NOT NULL,
    Shop_country STRING NOT NULL,
    Shop_postcode VARCHAR(15) NOT NULL,
    Shop_phone BIGINT NOT NULL,
    Shop_email VARCHAR(30) NOT NULL
)
USING DELTA;
```

- **Primary Key:** `Shop_id` (natural key, format: `SHL001` through `SHL014`)
- **Rows:** 14 UK shop locations
- **Constraint:** PK registered as `shops_pk` in Unity Catalog
- **Shop_email:** Auto-generated using `CONCAT(Shop_id, '@frasers.com')`

---

## 5. Staff (Dimension Table)

```sql
CREATE TABLE IF NOT EXISTS Staff (
    Staff_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY NOT NULL,
    Shop_id VARCHAR(20) NOT NULL,
    Staff_name STRING NOT NULL,
    Email_address STRING NOT NULL,
    Gender STRING NOT NULL,
    Date_of_birth DATE NOT NULL,
    Date_of_joining DATE NOT NULL,
    Job_Title STRING NOT NULL,
    Salary FLOAT NOT NULL,
    Status STRING NOT NULL,

    FOREIGN KEY (Shop_id) REFERENCES Shops(Shop_id)
)
USING DELTA;
```

- **Primary Key:** `Staff_id` (surrogate key, auto-incremented)
- **Foreign Key:** `Shop_id` references `Shops(Shop_id)`
- **Rows:** 40 staff records across various shop locations
- **Constraints:** PK registered as `staff_pk`, FK registered as `staff_shops_fk`
- **Job titles:** Store Manager, Assistant Manager, Sales Assistant, Customer Service Advisor

---

## 6. Dim_sales (Fact Table)

```sql
CREATE TABLE IF NOT EXISTS Dim_sales (
    Sales_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Sales_Date TIMESTAMP,
    Product_code STRING,
    Quantity INT,
    Customer_id BIGINT,
    Staff_id BIGINT,
    Shop_id VARCHAR(20),
    FOREIGN KEY (Product_code) REFERENCES FRASERS_GROUP.Products(Product_code),
    FOREIGN KEY (Customer_id) REFERENCES FRASERS_GROUP.Customers(Customer_id),
    FOREIGN KEY (Staff_id) REFERENCES FRASERS_GROUP.Staff(Staff_id),
    FOREIGN KEY (Shop_id) REFERENCES FRASERS_GROUP.Shops(Shop_id)
)
USING DELTA;
```

- **Primary Key:** `Sales_id` (surrogate key, auto-incremented)
- **Foreign Keys:** 4 FKs referencing all dimension tables
- **Rows:** 39 sales transactions spanning Jan-Mar 2026
- **Note:** This table must be created BEFORE inserting data (Cell 20 must run before Cell 19)

---

## 7. vw_sales (Analytical View)

```sql
CREATE VIEW vw_sales AS
SELECT
    s.sales_id,
    s.Sales_Date,
    c.Customer_name,
    p.Product_code,
    p.Product_description,
    s.Quantity,
    ROUND(s.Quantity * p.Product_price, 2) AS Total_Amount,
    st.Staff_name,
    sh.Shop_name
FROM Dim_sales s
INNER JOIN FRASERS_GROUP.Products p ON s.Product_code = p.Product_code
JOIN FRASERS_GROUP.Customers c ON s.Customer_id = c.Customer_id
JOIN FRASERS_GROUP.Staff st ON s.Staff_id = st.Staff_id
JOIN FRASERS_GROUP.Shops sh ON s.Shop_id = sh.Shop_id;
```

- **Type:** SQL View (denormalised)
- **Purpose:** Sales reporting with customer, product, staff, and shop details
- **Total_Amount:** Calculated as Quantity times Product_price, rounded to 2 decimal places

---

## 8. Execution Order

The tables should be created in the following order to satisfy foreign key dependencies:

1. Products (no FK dependencies)
2. Customers (no FK dependencies)
3. Shops (no FK dependencies)
4. Staff (FK to Shops)
5. Dim_sales (FK to Products, Customers, Staff, Shops)
6. vw_sales (view, depends on all tables above)