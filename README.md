# Mailingliste
Python-Script für die Mailingliste der [KSG Ilmenau](http://www.ksg-ilmenau.de).

## Vorbedingungen
Nach einem total-Crash unserer Hardware, wo ein php-Skript unsere Mailinglisten verwaltete, mussten wir improvisieren und etwas eigenes schnell auf die Beine stellen. Das Problem: [Mailman](https://www.gnu.org/software/mailman/) ist bei uns auf Grund der technischen Voraussetzungen nicht nutzbar.

Folgende Voraussetzungen:

 * geschlossene und offene Listen
 * Mailingliste hat eine eigene Mailbox
 * mehrere Mailinglisten teilen sich eine Mailbox
 * IMAP- und SMTP-Zugang
 * Mailbox-Ordnerstruktur:
   * INBOX
   * Spam
   * TooLarge

Wir haben unsere Mailboxen bei <img src="https://upload.wikimedia.org/wikipedia/commons/c/cd/1&1_logo.svg" alt="1&1" style="height:1em"/>. Ein Cron-Job führt das Shell-skript regelmäßig aus. Es greift via IMAP auf die jeweiligen Mailboxen zu und prüft alle Mails in der *INBOX*. Anschließend wird jede Mail analysiert, ob sie an eine definierte Listen-Mailadresse geschickt wurde, prüft die Daten und sendet sie weiter.

## mail.json
Konfigutionsdatei für die Mailingliste(n).
Unter *config* stehen die Zugriffsdaten für die Mailbox. Sind keine Nutzerdaten beim SMTP-Host angegeben, so wird eine anonymer Login versucht.

Jede Mailingliste erhält einen eigenen Unterzweig. Ihre Emailaddresse ist dabei der Schlüssel. Im Subtree *options* wird definiert, welche Emailadresse als Administrator angegeben werden soll (Mail-server werden dazu aufgefordert Fehlermeldungen etc. pp. dorthin zu schicken), wie der Prefix lautet (subject) und ob die Liste *geschlossen* (closed) oder *offen* (open) ist. 

Offene Listen brauchen einen Subtree *members*. Dies ist ein einfaches Array mit allen Emailadressen der Mitglieder. Jede eingehende Mail wird, bei erfolgreicher Spamprüfung, an alle Mitglieder weitergesendet.

Bei geschlossenen Listen können nur Mitglieder eine Mail auf die Liste schicken. Alle anderen Nutzer werden abgewiesen. Da einige Mitglieder mehr als nur eine Mailadresse haben, von denen sie senden, aber nur auf einer Adresse Mails erhalten wollen, gibt es den Subtree *alias*. Dies ist ein Array von Mailadressen, von denen auch Emails auf die Liste gesendet werden dürfen.

Besonders ist der Subtree *spam* und im config-Zweig *SPAM*. Dies sind Arrays von Emailadressen, die nicht senden dürfen. Sie werden ignoriert und stets unter in der Mailbox unter Spam gespeichert.
