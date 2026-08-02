# Notion Cooking List

Automates weekly mealprep by picking random recipes from Notion and populating a shopping list.

## What it does

1. Unchecks all previously marked `Todo` recipes in the My Recipes database
2. Picks 2 random recipes tagged with `Mealprep`
3. Marks them as `Todo = true` (they appear in the Weekly Cook! view)
4. Gathers ingredient names from both recipes' `Ingredients` relation
5. Clears the shopping list checklist on the Weekly Cook! page
6. Populates the checklist with deduplicated ingredient names

## Prerequisites

- Python 3.12+
- A Notion integration with read/write access to your recipe database and Weekly Cook! page
- The "Shopping list:" heading on your Weekly Cook! page must be a **callout** block (not H1)

## Setup

1. Create a `.env` file in the project root:
   ```
   NOTION_API_KEY=ntn_your_key_here
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python3 main.py
   ```

## GitHub Actions

To run via CI, add `NOTION_API_KEY` to your repository secrets and trigger the **Weekly Mealprep** workflow manually from the Actions tab. The workflow runs on `ubuntu-24.04-arm`.
