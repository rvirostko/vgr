## REPL - The Read-Evaluate-Print Loop

**TODO**

<a id="repl-cd"></a>

### Cd - Change the current working directory

---

* **cd** : changes to the user's home directory
* **cd *dir*** : changes to the given directory

Execution of statements are sandboxed to the current directory, so use
this command to change the location after starting a session.

### History - Display and Manage Command History

---

* **history** : display recent history
* **history --clear** : clear history
* **history --max *n*** : set the maximum commands saved

### Multiline - Multiline Editing Mode

---

* **multiline** : display the current setting
* **multiline [True | False]** : set multiline editing mode

When multiline editing mode is on, you can create multiple line statements to be executed.

Pressing return starts a new line rather than executing the command.

To execute commands in multiline editing mode, use *META-Return* instead.

### Prompt -  Change the REPL's Prompt

---

* **prompt** : print the template used to generate the interactive prompt
* **prompt *template*** : set the prompt to the template

The template supports a limited set of values that are defined by the
Bash Shell:

* **\d** - the date
* **\e** - the escape character
* **\h** - host name, short
* **\H** - host name, full
* **\n** - a new line
* **\t** - the time
* **\u** - user name
* **\w** - current directory
* **\W** - current directory, name only

On start up, the prompt template comes from **VGR_PROMPT** in the environment.
Changes made in the REPL are not persisted.

### Pwd - Print the current working directory

---

* **pwd** : prints the name of the current directory

Use **cwd** to change the current directory from withing the REPL.

### Shell - Open an OS sub-shell

---

* **shell** : open an interactive sub-shell
* **shell** *command* [*arg*]&hellip; : run the command in a sub-shell

**!** is an alias for **shell**

Note that changing the current working directory in a sub-shell does not
affect the value used in the REPL.
