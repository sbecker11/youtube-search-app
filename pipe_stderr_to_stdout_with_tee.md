# Piping stderr to stdout with tee

To pipe `stderr` (standard error) to `stdout` (standard output) while using `tee` to show either `stdout` or `stderr`, use the following syntax:

```sh
command 2>&1 | tee output.txt
```

This command will redirect `stderr` to `stdout`, and then pipe the combined output to `tee`, which will display it and save it to `output.txt`.

## Examples

### Redirecting and saving both stdout and stderr

```sh
ls non_existent_file 2>&1 | tee output.txt
```

This command will redirect the error message generated by `ls` to `stdout`, and then pipe the combined output to `tee`, which will display it and save it to `output.txt`.
