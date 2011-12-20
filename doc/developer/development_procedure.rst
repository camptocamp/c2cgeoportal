.. _development_procedure:


Development procedure
=====================

When we create a contribution to the project (c2cgeoportal or cgxp) the first 
thing that the developer do to create  new branch in the repository
``git checkout -b <branch_name>``.

Than the developer can to all he want in his branch.

When the contribution is ready he should pull it the the server 
``git pull origin <branch_name>`` an do a pull request from the 
github web interface.

An other developer review the contribution.

If it not OK a new commit will automatically be visible in the
pull request.

To permit to every body to do a review it shouldn't be merge 
(except for trivial bug fix) before 24h after the pull request.

Finally **only the main developer** who has the integration responsibility
merge it to the master branch. If an exception is needed because the 
main developer is not present it should serve the project not the
devloppers.

To be clean the main developer delete the branch to escape to have too 
many branches ``git branch origin :<branch_name>``.

