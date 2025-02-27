#!/usr/bin/env python3

import asyncio
import os
import csv
import logging  # Import the logging module
from google.cloud import resourcemanager_v3
from google.cloud import billing_v1  # Import Billing API client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_project_billing_account_name(project_id):
    """Fetches the billing account name for a given project ID."""
    billing_client = billing_v1.CloudBillingClient()
    project_name = f"projects/{project_id}"
    try:
        project_billing_info = billing_client.get_project_billing_info(name=project_name) # Async call
        billing_account_name = project_billing_info.billing_account_name
        logging.debug(f"Project ID: {project_id} - Billing Account Name fetched: {billing_account_name}") # Debug log
        return billing_account_name
    except Exception as e:
        logging.warning(f"Project ID: {project_id} - Billing Account Not Found or Error: {e}") # Warning log
        return "Billing Account Not Found" # Handle cases where billing info isn't accessible

async def fetch_project_details(project, session): # session is not used directly in this example but is good practice for aiohttp
    """Fetches project details including billing account and labels."""
    project_id = project.project_id
    project_display_name = project.display_name if project.display_name else project.project_id # Use project ID as fallback
    labels = project.labels if project.labels else {}
    logging.debug(f"Fetching details for Project ID: {project_id}, Display Name: {project_display_name}") # Debug log
    billing_account_name = get_project_billing_account_name(project_id) # Async call

    return {
        "Project Display Name": project_display_name,
        "Project ID": project_id,
        "Billing Account ID Name": billing_account_name,
        "Labels": labels
    }

async def list_projects_in_folder(folder_name, level, session, project_details_list):
    """Asynchronously lists projects in a folder and its subfolders recursively."""
    folder_client = resourcemanager_v3.FoldersClient()
    project_client = resourcemanager_v3.ProjectsClient()
    indent = "  " * level
    folder_id_numeric = folder_name.split('/')[-1] # Extract numeric folder ID

    logging.info(f"{indent}Processing Folder: {folder_id_numeric} - Resource Name: {folder_name}") # Info log

    try:
        project_request = resourcemanager_v3.ListProjectsRequest(
            parent=folder_name
        )
        page_result_projects = project_client.list_projects(request=project_request)
        projects = list(page_result_projects) # Convert iterator to list for concurrent processing
        logging.info(f"{indent}  Found {len(projects)} projects in folder: {folder_id_numeric}") # Info log

        # Fetch project details concurrently
        tasks = [fetch_project_details(project, session) for project in projects] # Pass session if using aiohttp
        project_details_results = await asyncio.gather(*tasks) # Await all tasks to complete
        project_details_list.extend(project_details_results) # Add results to the main list

        folder_request = resourcemanager_v3.ListFoldersRequest(
            parent=folder_name
        )
        page_result_folders = folder_client.list_folders(request=folder_request)

        for folder in page_result_folders:
            await list_projects_in_folder(folder.name, level + 1, session, project_details_list) # Recursive async call

    except Exception as e:
        logging.error(f"{indent}Error processing folder '{folder_name}': {e}") # Error log


async def get_all_projects_async(organization_id):
    """Asynchronously retrieves all projects in the organization and its folders."""
    project_client = resourcemanager_v3.ProjectsClient()
    project_details_list = [] # List to store dictionaries of project details
    logging.info(f"Starting to fetch projects for organization: {organization_id}") # Info log

    # Get projects directly under organization (optional - based on previous findings)
    logging.info("Fetching projects directly under organization...") # Info log
    org_request = resourcemanager_v3.ListProjectsRequest(
        parent=f"organizations/{organization_id}"
    )
    page_result_org_projects = project_client.list_projects(request=org_request)
    org_projects = list(page_result_org_projects)
    logging.info(f"Found {len(org_projects)} projects directly under organization.") # Info log
    org_tasks = [fetch_project_details(project, None) for project in org_projects] # No session needed for google-cloud-client
    org_project_details_results = await asyncio.gather(*org_tasks)
    project_details_list.extend(org_project_details_results)


    # Get projects recursively from folders
    logging.info("Fetching projects recursively from folders...") # Info log
    folder_client = resourcemanager_v3.FoldersClient()
    org_resource_name = f"organizations/{organization_id}"
    folder_request = resourcemanager_v3.ListFoldersRequest(parent=org_resource_name)
    page_result_top_level_folders = folder_client.list_folders(request=folder_request)

    top_level_folders = list(page_result_top_level_folders) # Convert iterator to list for folder processing
    folder_tasks = [list_projects_in_folder(folder.name, 1, None, project_details_list) for folder in top_level_folders] # No session needed for google-cloud-client
    await asyncio.gather(*folder_tasks) # Run folder processing tasks concurrently

    logging.info("Completed fetching projects from folders.") # Info log
    return project_details_list


def write_projects_to_csv(project_details_list, csv_filename="projects_output.csv"):
    """Writes project details to a CSV file."""
    csv_columns = ["Project Display Name", "Project ID", "Billing Account ID Name", "Labels"]
    try:
        logging.info(f"Writing project details to CSV file: {csv_filename}") # Info log
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for project_detail in project_details_list:
                writer.writerow(project_detail)
        logging.info(f"Project details written to: {csv_filename}") # Info log
    except Exception as e:
        logging.error(f"Error writing to CSV file: {e}") # Error log


async def main_async():
    organization_id = os.environ.get("ORGANIZATION_ID")
    if not organization_id:
        organization_id = "YOUR_ORGANIZATION_ID"  # Fallback, remind user to change

    if not organization_id or organization_id == "YOUR_ORGANIZATION_ID":
        print("Error: Please set your ORGANIZATION_ID...")
        return

    logging.info(f"Script started for organization: {organization_id}") # Info log
    project_details = await get_all_projects_async(organization_id)
    logging.info(f"Total projects found: {len(project_details)}") # Info log

    write_projects_to_csv(project_details)
    logging.info("Script completed.") # Info log


if __name__ == "__main__":
    asyncio.run(main_async())
