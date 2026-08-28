## REPL - The Read-Evaluate-Print Loop

**TODO**

<a id="repl-prompt"></a>

### Changing the prompt

---

You can customize the REPL's prompt by changing **env.VGR_PROMPT**.
The value is a *template* which may include fixed text and replacable
values. The template supports a limited set of values that are defined
by the Bash Shell:

* **\d** - the date
* **\e** - the escape character
* **\h** - host name, short
* **\H** - host name, full
* **\n** - a new line
* **\t** - the time, static
* **\u** - user name
* **\w** - current directory
* **\W** - current directory, name only

The initial prompt template comes from **VGR_PROMPT** in the environment.
Changes made in the REPL are not persisted.

```vgr
vgr> Exhibit env.VGR_PROMPT
env.VGR_PROMPT = -not defined-
vgr> Set env.VGR_PROMPT To r"\h:\u\n$"
my_host:user
$Unset env.VGR_PROMPT
vgr>
```

<a id="repl-cd"></a>

### Changing and displaying the current working directory

---

The **cd** and **pwd** commands, like in a shell, can be used to change
and display the current directory.

* **pwd** : display the current working directory
* **cd** : changes to the user's home directory
* **cd *dir*** : changes to the given directory

Changes made in the REPL are not persistent. When you
exit the REPL the current direction is the same as when you
launched the session.

<a id="repl-history"></a>

### Displaying and managing command history

---

The REPL maintains a history of executed commands.
You can move forward and back in the list of commands
using the up and down arrow. Additionally, `Control-R`
begins a reverse search of previous command.

The REPL's `history` command lets you work with that list.

* **history** : display recent history
* **history --clear** : clear history list
* **history --max *n*** : set the maximum commands saved
  for this REPL session

The REPL stores the history in a file defined by **VGR_HISTORY**
in the shell's enviornment or, if that is not set,
in **.vgr_history** in your home directory.

The size of the history file is defined by **VGR_HISTORY_SIZE**
in the shell's environment or, if this is not set,
a maximum of 100 entries.

While both of these environment variables may appear in **env**,
changing them will not affect the current session: use the **history**
command instead.

<a id="repl-multiline"></a>

### Multiline editing mode

---

* **multiline** : display the current setting
* **multiline [True | False]** : set multiline editing mode

When multiline editing mode is on, you can create multiple line statements to be executed.

Pressing return starts a new line rather than executing the command.

To execute commands in multiline editing mode, use *META-Return* instead.

<a id="repl-shell"></a>

### Interacting with an OS sub-shell

---

* **shell** : open an interactive sub-shell
* **shell** *command* [*arg*]&hellip; : run the command in a sub-shell

**!** is an alias for **shell**

Changing the current working directory in a sub-shell does not
affect the value used in the REPL.
