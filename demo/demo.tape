Output demo/demo.gif

Set FontSize 16
Set Width 900
Set Height 600
Set FontFamily "Ubuntu Mono"

Hide
Type "VIRTUAL_ENV_DISABLE_PROMPT=1 source .venv/bin/activate && clear"
Enter
Sleep 500ms
Show

Type "kx get pods -n kube-system"
Enter
Sleep 2.5s

Type "kx state"
Enter
Sleep 2s

Type "kx labels 1"
Enter
Sleep 2s

Type "kx logs 1 --tail=5"
Enter
Sleep 2.5s

Type "kx get deployments -n kube-system"
Enter
Sleep 2s

Type "kx describe 1"
Enter
Sleep 2.5s

Type "kx tree 1 --index"
Enter
Sleep 3s

Type "kx describe 3"
Enter
Sleep 2.5s

Type "kx state"
Enter
Sleep 2s
