.. _development_procedure:


Development procedure
=====================

When we create a contribution to the project (c2cgeoportal or cgxp) the first 
thing that the developer do to create  new branch in the repository
``git checkout master;git checkout -b <branch_name>``.

Than the developer can to all he want in his branch.

When the contribution is ready he should pull it the the server 
``git pull origin <branch_name>`` an do a pull request from the 
github web interface.

An other developer review the contribution.

If it not OK a new commit will automatically be visible in the
pull request.

To permit to every body to do a review it shouldn't be merge 
(except for trivial bug fix) before 24h after the pull request.

Finally **only the main developer** merge it to the master branch. 

By *main developer* we name the main developer of c2cgeoportal,
he should have a global view of the integration on all the projects to don't
brake them and make the transition as easy as possible.

If the main developer is not present and a merge should be done,
the merge can be done in collaboration the the main developer of the project,
the merge should serve the project not the developers.

To notify that it's merged the main developer will add a message in the pull
request.

To be clean the main developer delete the branch to escape to have too 
many branches ``git branch origin :<branch_name>``.

Additional notes
----------------

We are on GIT than let's use it. 

It's less critical on GIT than on SVN to have some unmerged code the 
developer can let the responsibility of the integrator (main developer) to 
merge it when it's the appropriated time.

If two people want to work on the same branch let's do it !

It you start a contribution related to an other contribution that she isn't
merged let's branch from this branch (test in progress).
