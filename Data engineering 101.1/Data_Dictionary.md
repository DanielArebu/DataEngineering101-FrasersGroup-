# Data Dictionary — FRASERS_GROUP

This document provides a column-by-column description of every table in the `FRASERS_GROUP` database.

---

## 1. Products

| Column | Data Type | Nullable | Key | Description |
| --- | --- | --- | --- | --- |
| Product_code | STRING | NOT NULL | PK | Unique product identifier (format: `21567/23/454`) |
| Product_name | STRING | NOT NULL | | Name of the product (e.g., "Lipstick") |
| Product_description | STRING | NOT NULL | | Detailed description (e.g., "Lipstick with a matte finish") |
| Product_category | STRING | NOT NULL | | Category grouping (e.g., "Makeup") |
| Product_price | FLOAT | NOT NULL | | Unit price in GBP (e.g., 24.99) |
| Product_colour | STRING | NOT NULL | | Colour variant (e.g., Pink, White, Black, Green, Yellow, Blue, Red) |
| Product_quantity | INT | NOT NULL | | Stock quantity on hand |

**Notes:** Quantity is accumulated via MERGE when new stock arrives through `NewProducts`.

---

## 2. NewProducts (Staging)

| Column | Data Type | Nullable | Key | Description |
| --- | --- | --- | --- | --- |
| Product_code | STRING | NOT NULL | PK | Unique product identifier (matches Products schema) |
| Product_name | STRING | NOT NULL | | Name of the product |
| Product_description | STRING | NOT NULL | | Detailed description |
| Product_category | STRING | NOT NULL | | Category grouping |
| Product_price | FLOAT | NOT NULL | | Updated unit price in GBP |
| Product_colour | STRING | NOT NULL | | Colour variant |
| Product_quantity | INT | NOT NULL | | Additional stock quantity to be merged |

**Notes:** Truncated after each MERGE operation. Used as the source table for SCD-Type-1 upserts into Products.

---

## 3. Customers

| Column | Data Type | Nullable | Key | Description |
| --- | --- | --- | --- | --- |
| Customer_id | BIGINT | NOT NULL | PK, IDENTITY | Auto-generated surrogate key (starts at 1, increment 1) |
| Customer_name | STRING | NOT NULL | | Full name of the customer |
| Customer_Postal | VARCHAR(15) | NOT NULL | | UK postal code (e.g., "NG20TN") |
| Customer_email | STRING | NOT NULL | | Email address (e.g., "danielarebu@outlook.com") |
| Customer_phone | BIGINT | NOT NULL | | Phone number (stored as integer) |
| Birth_date | DATE | NOT NULL | | Date of birth (YYYY-MM-DD) |
| Customer_gender | STRING | NOT NULL | | Gender ("Male" or "Female") |
| Membership_Type | STRING | NOT NULL | | Membership tier ("Premium" or "Standard") |
| Status | STRING | NOT NULL | | Account status ("Active") |

**Notes:** Age is calculated dynamically using `FLOOR(months_between(CURRENT_DATE(), Birth_date) / 12)`.

---

## 4. Shops

| Column | Data Type | Nullable | Key | Description |
| --- | --- | --- | --- | --- |
| Shop_id | VARCHAR(20) | NOT NULL | PK | Unique shop identifier (format: `SHL001` through `SHL014`) |
| Shop_name | STRING | NOT NULL | | Display name (e.g., "Shirebrook Vale Shop") |
| Shop_address | STRING | NOT NULL | | Street address |
| Shop_city | STRING | NOT NULL | | City (e.g., Shirebrook, Mansfield, Nottingham) |
| Shop_state | STRING | NOT NULL | | County/region (e.g., Derbyshire, Nottinghamshire) |
| Shop_country | STRING | NOT NULL | | Country (all "England") |
| Shop_postcode | VARCHAR(15) | NOT NULL | | UK postcode (e.g., "NG21 7AT") |
| Shop_phone | BIGINT | NOT NULL | | Internal phone extension number |
| Shop_email | VARCHAR(30) | NOT NULL | | Shop email, auto-generated as `CONCAT(Shop_id, '@frasers.com')` |

**Notes:** 14 shops across the UK including cities like Birmingham, Manchester, Liverpool, Leeds, Sheffield, Derby, Leicester, Coventry.

---

## 5. Staff

| Column | Data Type | Nullable | Key | Description |
| --- | --- | --- | --- | --- |
| Staff_id | BIGINT | NOT NULL | PK, IDENTITY | Auto-generated surrogate key (starts at 1, increment 1) |
| Shop_id | VARCHAR(20) | NOT NULL | FK -> Shops | Foreign key referencing Shops(Shop_id) |
| Staff_name | STRING | NOT NULL | | Full name of the staff member |
| Email_address | STRING | NOT NULL | | Email address (format: firstname.lastname@frasers.com) |
| Gender | STRING | NOT NULL | | Gender ("Male" or "Female") |
| Date_of_birth | DATE | NOT NULL | | Date of birth (YYYY-MM-DD) |
| Date_of_joining | DATE | NOT NULL | | Employment start date |
| Job_Title | STRING | NOT NULL | | Role (Store Manager, Assistant Manager, Sales Assistant, Customer Service Advisor) |
| Salary | FLOAT | NOT NULL | | Annual salary in GBP |
| Status | STRING | NOT NULL | | Employment status ("Active") |

**Notes:** 40 staff members across shops. Salary ranges from 23,800 (Sales Assistant) to 48,000 (Store Manager).

---

## 6. Dim_sales (Fact Table)

| Column | Data Type | Nullable | Key | Description |
| --- | --- | --- | --- | --- |
| Sales_id | BIGINT | NULL | PK, IDENTITY | Auto-generated surrogate key (starts at 1, increment 1) |
| Sales_Date | TIMESTAMP | NULL | | Date and time of the transaction (e.g., "2026-01-05 09:15:00") |
| Product_code | STRING | NULL | FK -> Products | Foreign key referencing Products(Product_code) |
| Quantity | INT | NULL | | Number of units sold |
| Customer_id | BIGINT | NULL | FK -> Customers | Foreign key referencing Customers(Customer_id) |
| Staff_id | BIGINT | NULL | FK -> Staff | Foreign key referencing Staff(Staff_id) |
| Shop_id | VARCHAR(20) | NULL | FK -> Shops | Foreign key referencing Shops(Shop_id) |

**Notes:** 39 sales transactions spanning January to March 2026. Total amount is calculated in the `vw_sales` view as `Quantity * Product_price`.

---

## 7. vw_sales (View)

| Column | Data Type | Source | Description |
| --- | --- | --- | --- |
| sales_id | BIGINT | Dim_sales | Sales transaction ID |
| Sales_Date | TIMESTAMP | Dim_sales | Transaction timestamp |
| Customer_name | STRING | Customers | Customer full name |
| Product_code | STRING | Products | Product identifier |
| Product_description | STRING | Products | Product description |
| Quantity | INT | Dim_sales | Units sold |
| Total_Amount | DOUBLE | Calculated | Quantity times Product_price, rounded to 2 decimal places |
| Staff_name | STRING | Staff | Staff member who processed the sale |
| Shop_name | STRING | Shops | Shop where the sale occurred |

**Notes:** This is a denormalised view joining Dim_sales with all four dimension tables using inner joins.