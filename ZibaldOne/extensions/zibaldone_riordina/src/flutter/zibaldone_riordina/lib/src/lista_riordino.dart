// ZibaldOne · lista da riordinare che scorre da sola quando il dito (o il mouse)
// che trascina un riquadro entra nella fascia alta o bassa della lista
// (KAN-133: «1/5 del telefono», uguale su PC e telefono).
//
// È la ReorderableListView di Flet (packages/flet, Apache-2.0) costruita con i
// soli widget di Flutter, più lo scorrimento ai bordi. Gli elementi restano
// figli Flet, quindi `ft.ReorderableDragHandle` funziona come con la lista
// standard.

import 'package:flet/flet.dart';
import 'package:flet/src/controls/scroll_notification_control.dart';
import 'package:flet/src/controls/scrollable_control.dart';
import 'package:flet/src/utils/keys.dart';
import 'package:flet/src/widgets/reorderable_item_scope.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/widgets.dart';

class ListaRiordinoControl extends StatefulWidget {
  final Control control;

  ListaRiordinoControl({Key? key, required this.control})
      : super(key: key ?? ValueKey("control_${control.id}"));

  @override
  State<ListaRiordinoControl> createState() => _ListaRiordinoState();
}

class _ListaRiordinoState extends State<ListaRiordinoControl>
    with SingleTickerProviderStateMixin {
  final ScrollController _controller = ScrollController();
  final GlobalKey _viewport = GlobalKey();
  late final Ticker _ticker;
  List<Control> _controls = [];

  bool _dragging = false;
  PointerEvent? _pointer; // the last event of the pointer that drags
  Duration _lastTick = Duration.zero;

  @override
  void initState() {
    super.initState();
    _controls = [...widget.control.children("controls")];
    _ticker = createTicker(_tick);
  }

  @override
  void didUpdateWidget(covariant ListaRiordinoControl oldWidget) {
    _controls = [...widget.control.children("controls")];
    super.didUpdateWidget(oldWidget);
  }

  @override
  void dispose() {
    _ticker.dispose();
    _controller.dispose();
    super.dispose();
  }

  void _start(int index) {
    _dragging = true;
    _lastTick = Duration.zero;
    if (!_ticker.isActive) _ticker.start();
    widget.control.triggerEvent("reorder_start", {"old_index": index});
  }

  void _stop() {
    _dragging = false;
    if (_ticker.isActive) _ticker.stop();
  }

  void _track(PointerEvent event) {
    _pointer = event.original ?? event;
  }

  /// Every frame of a drag: how deep the pointer is in the top or bottom band
  /// (0 outside, 1 at the edge) sets the speed of the scroll.
  void _tick(Duration elapsed) {
    final seconds = (elapsed - _lastTick).inMicroseconds / 1e6;
    _lastTick = elapsed;
    final pointer = _pointer;
    final box = _viewport.currentContext?.findRenderObject() as RenderBox?;
    if (!_dragging || pointer == null || box == null || !box.hasSize) return;
    if (!_controller.hasClients || seconds <= 0 || seconds > 0.1) return;

    final fraction =
        (widget.control.getDouble("edge_fraction", 0.2)!).clamp(0.05, 0.5);
    final speed = widget.control.getDouble("edge_speed", 1000)!;
    final height = box.size.height;
    final band = height * fraction;
    final y = box.globalToLocal(pointer.position).dy;
    double depth = 0;
    if (y < band) {
      depth = -(band - y) / band;
    } else if (y > height - band) {
      depth = (y - (height - band)) / band;
    }
    if (depth == 0) return;
    depth = depth.clamp(-1.0, 1.0);

    final position = _controller.position;
    final target = (position.pixels + depth * speed * seconds)
        .clamp(position.minScrollExtent, position.maxScrollExtent);
    if ((target - position.pixels).abs() < 0.5) return;
    position.jumpTo(target);
    // The list moves the other blocks only when the pointer moves: a still
    // pointer at the same place lets it recompute where the block would land.
    if (pointer is PointerMoveEvent) {
      GestureBinding.instance.handlePointerEvent(
          pointer.copyWith(delta: Offset.zero));
    }
  }

  /// The item is its own handle: the mouse takes it at once, the finger (or
  /// the stylus) only after `touch_delay` seconds of holding, so that a swipe
  /// before then scrolls the page (KAN-138).
  void _down(BuildContext context, int index, PointerDownEvent event) {
    final list = SliverReorderableList.maybeOf(context);
    if (list == null) return;
    final immediate = event.kind == PointerDeviceKind.mouse ||
        event.kind == PointerDeviceKind.trackpad;
    final delay = Duration(
        milliseconds:
            ((widget.control.getDouble("touch_delay", 0.3)!).clamp(0.05, 2.0) *
                    1000)
                .round());
    final MultiDragGestureRecognizer recognizer = immediate
        ? ImmediateMultiDragGestureRecognizer(debugOwner: this)
        : DelayedMultiDragGestureRecognizer(delay: delay, debugOwner: this);
    recognizer.gestureSettings = MediaQuery.maybeGestureSettingsOf(context);
    list.startItemDragReorder(index: index, event: event, recognizer: recognizer);
  }

  Widget _item(BuildContext context, int index) {
    final control = _controls[index];
    final keyValue = control.getKey("key")?.value ?? control.id;
    return ReorderableItemScope(
      key: ValueKey(keyValue),
      index: index,
      child: MouseRegion(
        cursor: SystemMouseCursors.grab,
        child: Listener(
          behavior: HitTestBehavior.translucent,
          onPointerDown: (event) => _down(context, index, event),
          child: ControlWidget(key: ValueKey(keyValue), control: control),
        ),
      ),
    );
  }

  Widget _lifted(Widget child, int index, Animation<double> animation) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) => DecoratedBox(
        decoration: BoxDecoration(boxShadow: [
          BoxShadow(
            color: const Color(0x66000000),
            blurRadius: 16 * animation.value,
            offset: Offset(0, 6 * animation.value),
          ),
        ]),
        child: child,
      ),
      child: child,
    );
  }

  @override
  Widget build(BuildContext context) {
    final control = widget.control;
    final header = control.buildWidget("header");
    final footer = control.buildWidget("footer");
    final padding = control.getPadding("padding");

    void onReorder(int oldIndex, int newIndex) {
      setState(() {
        if (oldIndex < newIndex) newIndex -= 1;
        _controls.insert(newIndex, _controls.removeAt(oldIndex));
      });
      control.triggerEvent(
          "reorder", {"old_index": oldIndex, "new_index": newIndex});
    }

    Widget list = SliverReorderableList(
      itemCount: _controls.length,
      itemBuilder: _item,
      onReorder: onReorder,
      onReorderStart: _start,
      onReorderEnd: (index) {
        _stop();
        control.triggerEvent("reorder_end", {"new_index": index});
      },
      proxyDecorator: _lifted,
      // Flutter's own scroll starts as soon as the edge of the dragged block
      // leaves the screen (at once with a tall block): made too slow to see,
      // so the band below decides.
      autoScrollerVelocityScalar: 0.05,
    );
    if (padding != null) list = SliverPadding(padding: padding, sliver: list);

    Widget child = CustomScrollView(
      key: _viewport,
      controller: _controller,
      clipBehavior:
          control.getClipBehavior("clip_behavior", Clip.hardEdge)!,
      slivers: [
        if (header != null) SliverToBoxAdapter(child: header),
        list,
        if (footer != null) SliverToBoxAdapter(child: footer),
      ],
    );

    child = ScrollableControl(
        control: control,
        scrollDirection: Axis.vertical,
        scrollController: _controller,
        child: child);
    if (control.hasEventHandler("scroll")) {
      child = ScrollNotificationControl(control: control, child: child);
    }
    child = Listener(
      behavior: HitTestBehavior.translucent,
      onPointerDown: _track,
      onPointerMove: _track,
      onPointerUp: (_) => _pointer = null,
      onPointerCancel: (_) => _pointer = null,
      child: child,
    );
    return LayoutControl(control: control, child: child);
  }
}
