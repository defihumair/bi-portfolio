import pandas as pd
import os
import git  # Ensure you have GitPython installed

# Load your new data
new_data_path = "E:\\DashApp\\ContainerActivity.xlsx"  # Update this path to your new data file
data = pd.read_excel(new_data_path)

# Save the updated data to your repository
repo_path = "E:\\DashApp"  # Path to your repository
data.to_excel(os.path.join(repo_path, "ContainerActivity.xlsx"), index=False)

# Commit and push changes
repo = git.Repo(repo_path)
repo.git.add("ContainerActivity.xlsx")
repo.index.commit("Automated update of ContainerActivity.xlsx")
repo.git.push("origin", "main")  # or master, depending on your branch name
