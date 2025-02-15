# Using EOF to Define End of Text

To use `EOF` to define the end of text to input in a Unix-based system, you can use a here document. A here document allows you to redirect a block of text to a command or file.

## Syntax

```sh
command <<EOF
your text
EOF
```

Here, `EOF` is a delimiter that marks the beginning and end of the text block. You can replace `EOF` with any other delimiter.

## Examples

### Redirecting a block of text to a command

```sh
cat <<EOF
This is a block of text.
It will be redirected to the `cat` command.
EOF
```

This command will redirect the block of text to the `cat` command, which will display it.

### Redirecting a block of text to a file

```sh
cat <<EOF > output.txt
This is a block of text.
It will be saved to `output.txt`.
EOF
```

This command will redirect the block of text to the `cat` command, which will save it to `output.txt`.
