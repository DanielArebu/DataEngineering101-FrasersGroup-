# Data Engineering 101 — Frasers Group Retail Database

This repository contains a complete data engineering project that builds a relational retail database for **Frasers Group** using Databricks Delta Lake and Unity Catalog.

## Project Summary

The project demonstrates the full data engineering lifecycle: schema design, dimension/fact table modelling, foreign key constraints, MERGE upserts, IDENTITY columns, and analytical views. The database consists of 6 tables (4 dimension, 1 staging, 1 fact) and 1 analytical view within the `FRASERS_GROUP` schema.

## Repository Structure

```
DataEngineering101-FrasersGroup-
├── Data Engineering 101.py          # Main Databricks notebook (22 cells)
├── Documents/
│   ├── Project_Overview.md          # High-level architecture, objectives, workflows
│   ├── Database_Schema.md           # Complete table DDL, constraints, ERD
│   └── Data_Dictionary.md          # Column-by-column descriptions for all tables
├── LICENSE
└── README.md
```

## Tables

| Table | Type | Primary Key | Rows |
| --- | --- | --- | --- |
| Products | Dimension | Product_code (STRING) | 7 |
| Customers | Dimension | Customer_id (BIGINT IDENTITY) | 3 |
| Shops | Dimension | Shop_id (VARCHAR(20)) | 14 |
| Staff | Dimension | Staff_id (BIGINT IDENTITY) | 40 |
| Dim_sales | Fact | Sales_id (BIGINT IDENTITY) | 39 |
| NewProducts | Staging | Product_code (STRING) | 0 (truncated after MERGE) |

## Key Features

- Delta Lake tables with `USING DELTA`
- Primary and foreign key constraints in Unity Catalog
- `GENERATED ALWAYS AS IDENTITY` for surrogate keys
- `MERGE INTO` for SCD-Type-1 upserts with quantity accumulation
- Analytical view (`vw_sales`) with denormalised sales reporting
- Date functions for dynamic age calculation
- `TRUNCATE TABLE` for staging table cleanup

## How to Run

1. Clone this repository into a Databricks Git folder
2. Open `Data Engineering 101` in the Databricks notebook editor
3. Run all cells from top to bottom
4. Query `vw_sales` to view the denormalised sales report

## Documentation

Detailed documentation is available in the [Documents](Documents/) folder:

- [Project Overview](Documents/Project_Overview.md) — Architecture, objectives, and key workflows
- [Database Schema](Documents/Database_Schema.md) — Complete DDL, constraints, and ERD
- [Data Dictionary](Documents/Data_Dictionary.md) — Column descriptions for all tables

## Technology Stack

| Component | Technology |
| --- | --- |
| Cloud Platform | Databricks on AWS |
| Storage | Delta Lake (Unity Catalog) |
| Compute | Serverless Interactive Cluster |
| Query Language | Databricks SQL |
| Version Control | GitHub |



## License

See the [LICENSE](LICENSE) file for details.
