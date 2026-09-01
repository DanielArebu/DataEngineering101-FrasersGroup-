# Project Overview — Data Engineering 101: Frasers Group Retail Database

## 1. Introduction

This project implements a complete relational retail database for **Frasers Group** using Databricks Delta Lake. It demonstrates core data engineering skills including schema design, dimension/fact table modelling, foreign key constraints, MERGE upserts, IDENTITY columns, and analytical views.

The database is built within the `FRASERS_GROUP` schema in Unity Catalog and consists of six tables (five dimension/staging tables and one fact table) plus one analytical view.

---

## 2. Objectives

- Design a normalised star-schema database for a retail business
- Implement referential integrity using primary and foreign key constraints in Unity Catalog
- Demonstrate SCD-Type-1 upserts using `MERGE INTO` with quantity accumulation
- Use `GENERATED ALWAYS AS IDENTITY` for surrogate keys on Customers, Staff, and Sales tables
- Build a denormalised analytical view (`vw_sales`) for reporting
- Showcase Databricks SQL features: date functions, string concatenation, rounding, and grouping

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRASERS_GROUP Schema                  │
│                     (Unity Catalog)                      │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │  Products  │  │ Customers  │  │      Shops          │  │
│  │ (Dim)      │  │ (Dim)      │  │ (Dim)               │  │
│  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘  │
│        │               │                  │              │
│        │               │         ┌────────┴───────────┐  │
│        │               │         │      Staff         │  │
│        │               │         │ (Dim, FK → Shops)  │  │
│        │               │         └────────┬───────────┘  │
│        │               │                  │              │
│        └───────┬───────┴──────────────────┘              │
│                │                                        │
│        ┌───────┴──────────┐  ┌─────────────────────┐   │
│        │    Dim_sales       │  │   NewProducts       │   │
│        │ (Fact, 4 FKs)      │  │ (Staging)           │   │
│        └────────────────────┘  └─────────────────────┘   │
│                │                                        │
│        ┌───────┴──────────┐                             │
│        │    vw_sales       │  (Analytical View)          │
│        │ (Denormalised)     │                             │
│        └────────────────────┘                             │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Data Model Summary

| Table | Type | Grain | Primary Key | Rows |
| --- | --- | --- | --- | --- |
| Products | Dimension | One row per product | Product_code (STRING) | 7 |
| Customers | Dimension | One row per customer | Customer_id (BIGINT IDENTITY) | 3 |
| Shops | Dimension | One row per shop location | Shop_id (VARCHAR(20)) | 14 |
| Staff | Dimension | One row per staff member | Staff_id (BIGINT IDENTITY) | 40 |
| Dim_sales | Fact | One row per sales transaction | Sales_id (BIGINT IDENTITY) | 39 |
| NewProducts | Staging | Temporary upsert source | Product_code (STRING) | 0 (truncated after MERGE) |

---

## 5. Foreign Key Relationships

| Child Table | Child Column | Parent Table | Parent Column |
| --- | --- | --- | --- |
| Staff | Shop_id | Shops | Shop_id |
| Dim_sales | Product_code | Products | Product_code |
| Dim_sales | Customer_id | Customers | Customer_id |
| Dim_sales | Staff_id | Staff | Staff_id |
| Dim_sales | Shop_id | Shops | Shop_id |

---

## 6. Key Workflows

### 6.1 Products MERGE (SCD-Type-1 Upsert)

The `NewProducts` staging table holds incoming product records. The `MERGE INTO` statement:

- **When matched** (Product_code exists): Updates name and price, and **accumulates** quantity (`target.Product_quantity + source.Product_quantity`)
- **When not matched**: Inserts the new product
- After the MERGE, the staging table is truncated (`TRUNCATE TABLE NewProducts`)

### 6.2 Sales Analysis (vw_sales View)

The `vw_sales` view joins the fact table (`Dim_sales`) with all four dimension tables to produce a denormalised sales report containing:
- Sales ID and date
- Customer name
- Product code and description
- Quantity and total amount (quantity × product price, rounded to 2 decimal places)
- Staff name
- Shop name

### 6.3 Customer Age Calculation

Customer age is computed dynamically using `FLOOR(months_between(CURRENT_DATE(), Birth_date) / 12)`.

---

## 7. Technology Stack

| Component | Technology |
| --- | --- |
| Cloud Platform | Databricks on AWS |
| Storage | Delta Lake (Unity Catalog) |
| Compute | Serverless Interactive Cluster |
| Query Language | Databricks SQL (within Python notebook) |
| Version Control | GitHub (DanielArebu/DataEngineering101-FrasersGroup-) |

---

## 8. Prerequisites

- Databricks workspace with Unity Catalog enabled
- `CREATE DATABASE` and `CREATE TABLE` permissions on the target catalog
- A serverless or all-purpose compute cluster

---

## 9. How to Run

1. Clone this repository into a Databricks Git folder
2. Open the notebook `Data Engineering 101` in the Databricks notebook editor
3. Run all cells top to bottom:
   - Cell 2 creates the `FRASERS_GROUP` database
   - Cell 3 sets the active schema
   - Cells 4–22 create tables, insert data, MERGE, and build the analytical view
4. Query `vw_sales` to view the denormalised sales report

---

## Author

**Daniel Arebu**
Data Engineering 101 Project
GitHub: [DanielArebu](https://github.com/DanielArebu)

---

## License

See the [LICENSE](../LICENSE) file in the repository root.