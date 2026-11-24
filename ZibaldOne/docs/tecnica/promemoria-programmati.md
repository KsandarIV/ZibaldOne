# Promemoria programmati in anticipo (0.3.6)

Su Windows i promemoria suonano anche con l'app chiusa grazie alle attività pianificate (`notify/windows_tasks.py`). Su Android `android-notify` mostra le notifiche solo mentre l'app gira: per averle ad app chiusa serve che il sistema le faccia partire da solo (AlarmManager).

`plan_alarms(config, now, days=7)` in `core/reminders.py` calcola cosa registrare: l'elenco dei prossimi promemoria (`PlannedAlarm`: `code`, `at`, `reminder`), con le stesse regole di sempre (momenti attivi, giorni scelti, ore silenziose, finestra). È puro: non legge orologio, disco o rete.

- Il `code` è stabile (stesso momento, stesso giorno, stesso numero): serve a sostituire o annullare un allarme già registrato.
- Non sa se il diario di oggi sarà già scritto: l'app ricalcola il piano ogni volta che si apre o cambiano le impostazioni, e al momento dello scatto si scarta il promemoria di un momento già scritto.
- I messaggi non contengono mai testo delle voci; le tappe di serie (milestone) non si pianificano.

Non è ancora collegato ad AlarmManager: la parte nativa Android (ricevitore, permesso per allarmi esatti, riavvio del telefono) va fatta e provata su un telefono vero.
