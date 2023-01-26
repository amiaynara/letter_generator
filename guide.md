1. Create a local branch.(ken-local) and move to that new branch
    git checkout -b ken-local
2. Make the changes to the local copy of your flask app (in .html files or in .py file). After
    we are satisfied with the changes we now will upload(push) the changes to github and then to pythonanywhere.
    ```
    git status 
    git add <list of files separated by spaces>
    ```
    for example: 
    ```
    git add templates/choices.html
    git commit -m 'Change the name of the site on the /choices page'
    ```
