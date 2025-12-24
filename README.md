# Natural Gas Intelligence & Trading System

An automated, data-driven system for analyzing and monitoring **Natural Gas (NG)** markets using fundamentals, weather intelligence, and quantitative signals.  
The project is designed for **traders, analysts, and researchers** who want a reliable pipeline for decision-support and automated reporting.

---

## Overview

Natural Gas is a globally traded energy commodity with demand highly sensitive to **weather, storage levels, and supply–demand dynamics**.  
This system aggregates multiple public and programmatic data sources, processes them into structured intelligence, and generates actionable insights.

The architecture is modular, automation-friendly, and suitable for **24/7 deployment**.

---

## Core Features

- **EIA Storage Data**
  - Automated scraping of weekly EIA storage reports
  - Current vs 5-year average comparison
  - Surprise analysis (actual vs market expectation)

- **Weather & Temperature Intelligence**
  - GFS temperature model ingestion
  - Region-wise temperature extraction using image analysis
  - HDD / CDD regime classification
  - Climate regime interpretation (bullish / bearish / neutral)

- **Supply–Demand Context**
  - Storage momentum
  - Seasonal demand signals
  - Structural tightness/looseness detection

- **Automated Market Commentary**
  - AI-generated professional market commentary
  - Structured report payloads (JSON → text)
  - Suitable for email, dashboards, or social posting

- **Automation & Scheduling**
  - GitHub Actions / cron-based execution
  - Serverless-friendly architecture
  - Designed for ₹0/month deployment setups

---

## Tech Stack

- **Language:** Python 3.10+
- **Core Libraries:**
  - `requests`
  - `pandas`
  - `numpy`
  - `Pillow`
  - `datetime`
- **Data Sources:**
  - EIA (Energy Information Administration)
  - GFS Weather Model
  - DegreeDays APIs
- **AI Layer:**
  - LLM-based market commentary generation
- **Automation:**
  - GitHub Actions / Cron
  - PythonAnywhere / Cloud VM compatible

---

## Project Structure

