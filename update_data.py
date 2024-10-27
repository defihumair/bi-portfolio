import pandas as pd
import os
import git  # Make sure GitPython is installed

# Define file paths
local_file_path = r"E:\DashApp\ContainerActivity.xlsx"
repo_path = r"E:\DashApp"  # Path to your local Git repo

# Open and save the updated file to ensure it's in the latest state
data = pd.read_excel(local_file_path)
data.to_excel(os.path.join(repo_path, "ContainerActivity.xlsx"), index=False)

# Commit and push the changes
repo = git.Repo(repo_path)
repo.git.add("ContainerActivity.xlsx")
repo.index.commit("Automated update of ContainerActivity.xlsx")
repo.git.push("origin", "master")  # Push to your remote branch (master or main)
