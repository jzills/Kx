Output demo/demo.gif

Set FontSize 13
Set Width 900
Set Height 600
Set FontFamily "JetBrains Mono"

Type "source .venv/bin/activate && clear"
Enter
Sleep 500ms

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

Type "kx tree 1 --index"
Enter
Sleep 3s
