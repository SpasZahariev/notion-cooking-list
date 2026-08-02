import json
import random
import requests
from dotenv import load_dotenv
import os

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
API_BASE = "https://api.notion.com"
DB_ID = "a0f09e03-55ca-4fc2-a4a3-58c697e0c5ab"
WEEKLY_COOK_PAGE_ID = "1dd1da327a144437a52e57fa695d9edb"
NUM_RECIPES = 2

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def api_post(path, body=None):
    resp = requests.post(f"{API_BASE}{path}", headers=HEADERS, json=body or {})
    resp.raise_for_status()
    return resp.json()


def api_patch(path, body=None):
    resp = requests.patch(f"{API_BASE}{path}", headers=HEADERS, json=body or {})
    resp.raise_for_status()
    return resp.json()


def api_delete(path):
    resp = requests.delete(f"{API_BASE}{path}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def query_db(db_id, filter_obj=None):
    body = {}
    if filter_obj:
        body["filter"] = filter_obj
    results = []
    while True:
        resp = api_post(f"/v1/databases/{db_id}/query", body)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        body["start_cursor"] = resp["next_cursor"]
    return results


def get_page(page_id):
    return api_post(f"/v1/pages/{page_id}")


def update_todo(page_id, todo_value):
    api_patch(
        f"/v1/pages/{page_id}",
        {"properties": {"Todo": {"checkbox": todo_value}}},
    )


def get_blocks(block_id):
    results = []
    while True:
        resp = api_post(f"/v1/blocks/{block_id}/children")
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        resp = api_post(
            f"/v1/blocks/{block_id}/children", {"start_cursor": resp["next_cursor"]}
        )
    return results


def delete_block(block_id):
    api_delete(f"/v1/blocks/{block_id}")


def append_blocks(parent_id, children):
    api_patch(
        f"/v1/blocks/{parent_id}/children",
        {"children": children},
    )


def get_title(page_obj):
    props = page_obj.get("properties", {})
    title_prop = props.get("Name", {}) or props.get("title", {})
    rich_text = title_prop.get("rich_text", [])
    if rich_text:
        return rich_text[0].get("plain_text", "")
    return ""


def main():
    print(f"=== Weekly Mealprep Automation ===")

    # Step 1: Uncheck all existing Todo recipes
    print("\n[1] Unchecking old Todo recipes...")
    todo_filter = {"property": "Todo", "checkbox": {"equals": True}}
    todo_pages = query_db(DB_ID, todo_filter)
    for page in todo_pages:
        pid = page["id"]
        title = get_title(page)
        update_todo(pid, False)
        print(f"  Unchecked: {title}")
    if not todo_pages:
        print("  No existing Todo recipes found.")

    # Step 2: Pick 2 random Mealprep recipes
    print("\n[2] Picking random Mealprep recipes...")
    mealprep_filter = {"property": "Tags", "multi_select": {"contains": "Mealprep"}}
    mealprep_pages = query_db(DB_ID, mealprep_filter)
    if len(mealprep_pages) < NUM_RECIPES:
        print(f"  ERROR: Only {len(mealprep_pages)} Mealprep recipes found, need {NUM_RECIPES}")
        return
    selected = random.sample(mealprep_pages, NUM_RECIPES)
    for page in selected:
        title = get_title(page)
        print(f"  Selected: {title}")

    # Step 3: Mark selected as Todo
    print("\n[3] Marking selected recipes as Todo...")
    for page in selected:
        pid = page["id"]
        title = get_title(page)
        update_todo(pid, True)
        print(f"  Checked: {title}")

    # Step 4: Gather ingredients from selected recipes
    print("\n[4] Gathering ingredients...")
    ingredient_names = set()
    for page in selected:
        props = page.get("properties", {})
        ingredients_prop = props.get("Ingredients", {})
        relation_ids = [r["id"] for r in ingredients_prop.get("relation", [])]
        for ing_id in relation_ids:
            ing_page = get_page(ing_id)
            name = get_title(ing_page)
            if name:
                ingredient_names.add(name)
    sorted_ingredients = sorted(ingredient_names)
    print(f"  Found {len(sorted_ingredients)} unique ingredients:")
    for name in sorted_ingredients:
        print(f"    - {name}")

    # Step 5: Clear shopping list on Weekly Cook page
    print("\n[5] Clearing shopping list on Weekly Cook!...")
    blocks = get_blocks(WEEKLY_COOK_PAGE_ID)
    callout_index = None
    for i, block in enumerate(blocks):
        if block.get("type") == "callout":
            rich_text = block.get("callout", {}).get("rich_text", [])
            text = "".join(rt.get("plain_text", "") for rt in rich_text).strip()
            if text == "Shopping list:":
                callout_index = i
                break

    if callout_index is None:
        print("  WARNING: Could not find 'Shopping list:' callout block.")
        print("  Make sure the heading on Weekly Cook! is a callout with text 'Shopping list:'")
    else:
        blocks_to_delete = blocks[callout_index + 1:]
        for block in blocks_to_delete:
            delete_block(block["id"])
            print(f"  Deleted block: {block['id']}")
        if not blocks_to_delete:
            print("  Shopping list was already empty.")

    # Step 6: Populate checklist with ingredients
    print("\n[6] Populating shopping list...")
    children = []
    for name in sorted_ingredients:
        children.append({
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": name}}],
                "checked": False,
            },
        })

    if children:
        append_blocks(WEEKLY_COOK_PAGE_ID, children)
        print(f"  Added {len(children)} items to shopping list.")
    else:
        print("  No ingredients to add.")

    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
