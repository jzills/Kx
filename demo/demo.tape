Output demo/demo.gif

Set FontSize 16
Set Width 1200
Set Height 750
Set FontFamily "Ubuntu Mono"
Set BackgroundColor "#000000"
Set ForegroundColor "#e6edf3"
Set Framerate 30

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
