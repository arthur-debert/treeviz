3viz, a terminal ast vizualizer for document based ASTs.

3viz is designed to simplify re

1.. Codebase rules:
  
  1. Let's keep the repo clean, do not:
      - create status md files. Ideally we should use git commit, gh issues (if you're working on one) or pr requests (ifor you branch) to document it, anything BUT these. They do not belong under source control and they do not register correctly the history of the work being done.
      - same for temporary scripts: if you need , put them in $PROJECT_ROOT/local (which don't get source controlled and are periodically purged)
    
  2. Code Comments
      We love comments and they are essential, but only the useful ones.
      Restating what the fucntion or variable name already tells you is useless, the code already has this information.
      Here are worth while comments that:
        *Describe the general design or function of a feature or module, with a good overview (not necessarily code related)
        - That document design decisions or use cases for that code and that explains why that code is there.
        - That explain a few of very cryptics lines (very rate in python)

  3. NO BACKWARDS COMPATIBILITY NOR ADAPTERS NOR DEPRECATED ANYTHING
    This is a pre-release software, there is no client app usage, there is nothing to keep backwards compatibility.
    Tasks that require refactoring , reorganizzing and renaming things INCLUDE updating callers AND tests.
    Creating layers and adapters to avoid doing the udpating work will:
      - Make the code much harder: now you just multiplied all paths by 2
      - As this pile up, it becomes geometric, and now you have 64 variants of the same feature depenidng on which layers they tigger
      - Becomes harder to maintain, to test, to rason and to bring new developers for speed.

    Therefore unless explicitly asked to in the task description, do not keep those.

8. Checklist before commiting:

- Are there any test failures? Did you skip pre-commit checks or have tempered quality assurances?
- Tests are integration based, have ad-hoc in test files input stirngs and do not leverage fixtures that are available?
- Did you litter the repo with status updates, thow-away scripts oustide the local directory?
- When working on gh issue; dis you forget to reference the issue on the commit message?
- Did you make anything deprecated ?
- Did you hardode logging levels or other setup instead of using flags?

 If the answer to any of this is yes, stop and fix it, don't commit unless all answers above are NO.

9. How we work:

- atomic commits: commits should have integritry, that is   a stand alone part of the work (and it's tests) must be functional, but it's entirely ok (and encouraged) to commit larger tasks in several commits.
- do not "write lots of code " then " test at the end" , test code as you write, fucntion by function. Not only this makes for a better tested codebase, but it avoids broken states that are hard to commmit and merge.
- always do work on feature branches. If you are working for one specific gh issue, use $gh issue develop -c -> to generate the branch correctly.
- After the task is done, submit the pr, and using gh cli, verify the pr is clean (checks pass and is mergeable), using the cli to debug wofklows if needed.

  10. Writing Style and documentation
    - NO MARKDOWN, anywhere.  Use plain text, no **bold**o
    - No emojis (unicode symbols that aid in comprehension are are monochrome: yes!)

- No need to be enterprise or tout generalities about benefits (Modularized code is more scalable! etc) , we are experienced developers and we understand this.
- We like compact , informational and readable writing. You can follow the general feel in this document  (humor is good, though)
