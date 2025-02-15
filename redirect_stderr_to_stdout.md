# Redirecting stderr to stdout

To redirect `stderr` (standard error) to `stdout` (standard output) in a Unix-based system, use the following syntax:

```sh
command 2>&1
```

Here, `2` represents `stderr` and `1` represents `stdout`. The `>&` operator redirects `stderr` to `stdout`.

## Examples

### Redirecting error messages to standard output

```sh
ls non_existent_file 2>&1
```

This command will redirect the error message generated by `ls` to the standard output.

### Saving both stdout and stderr to a file

```sh
command > output.txt 2>&1
```

This command will redirect both `stdout` and `stderr` to `output.txt`.
