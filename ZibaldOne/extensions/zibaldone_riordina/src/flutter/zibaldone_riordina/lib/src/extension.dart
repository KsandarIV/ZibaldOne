import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'lista_riordino.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "ZibaldoneListaRiordino":
        return ListaRiordinoControl(key: key, control: control);
      default:
        return null;
    }
  }
}
