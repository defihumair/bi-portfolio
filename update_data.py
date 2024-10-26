import pandas as pd
import os
import git  # Ensure you have GitPython installed

# Load your new data
new_data_path = "E:\\DashApp\\ContainerActivity.xlsx"  # Path to your data
data = pd.read_excel(new_data_path)

# Save the updated data to your repository
repo_path = "E:\\DashApp"  # Path to your repo
data.to_excel(os.path.join(repo_path, "ContainerActivity.xlsx"), index=False)

# Commit and push changes
repo = git.Repo(repo_path)
repo.git.add("ContainerActivity.xlsx")
repo.index.commit("Automated update of ContainerActivity.xlsx")
repo.git.push("origin", "master")  # or main, depending on your branch name
