import AppKit
import AVFoundation
import CoreGraphics
import CoreVideo
import Foundation
import ImageIO
import UniformTypeIdentifiers

let width = 1920
let height = 1080
let fps: Int32 = 60
let sourceDurationSeconds = 42.0
let speedFactor = 1.5
let durationSeconds = sourceDurationSeconds / speedFactor
let totalFrames = Int(durationSeconds * Double(fps))

let defaultOutput = "/Users/corld/Desktop/软件系统开发/Facebook/promo/ai-qa-community-enterprise-saas-promo.mp4"
let defaultPoster = "/Users/corld/Desktop/软件系统开发/Facebook/promo/ai-qa-community-enterprise-saas-promo-poster.png"

let outputURL = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : defaultOutput)
let posterURL = URL(fileURLWithPath: CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : defaultPoster)

struct Palette {
    static let ink = NSColor(calibratedRed: 0.05, green: 0.08, blue: 0.16, alpha: 1)
    static let muted = NSColor(calibratedRed: 0.35, green: 0.40, blue: 0.50, alpha: 1)
    static let blue = NSColor(calibratedRed: 0.05, green: 0.22, blue: 0.62, alpha: 1)
    static let blueSoft = NSColor(calibratedRed: 0.13, green: 0.38, blue: 0.95, alpha: 1)
    static let purple = NSColor(calibratedRed: 0.48, green: 0.25, blue: 0.95, alpha: 1)
    static let purpleSoft = NSColor(calibratedRed: 0.62, green: 0.44, blue: 1.0, alpha: 1)
    static let cyan = NSColor(calibratedRed: 0.06, green: 0.72, blue: 0.82, alpha: 1)
    static let white = NSColor.white
    static let panel = NSColor(calibratedRed: 1, green: 1, blue: 1, alpha: 0.84)
    static let border = NSColor(calibratedRed: 0.78, green: 0.84, blue: 0.94, alpha: 0.46)
}

func clamp(_ value: CGFloat, _ minValue: CGFloat = 0, _ maxValue: CGFloat = 1) -> CGFloat {
    return max(minValue, min(maxValue, value))
}

func smoothstep(_ edge0: Double, _ edge1: Double, _ value: Double) -> CGFloat {
    if edge0 == edge1 {
        return value >= edge1 ? 1 : 0
    }
    let x = clamp(CGFloat((value - edge0) / (edge1 - edge0)))
    return x * x * (3 - 2 * x)
}

func easeOut(_ value: CGFloat) -> CGFloat {
    let x = clamp(value)
    return 1 - pow(1 - x, 3)
}

func easeInOut(_ value: CGFloat) -> CGFloat {
    let x = clamp(value)
    return x < 0.5 ? 4 * x * x * x : 1 - pow(-2 * x + 2, 3) / 2
}

func lerp(_ a: CGFloat, _ b: CGFloat, _ t: CGFloat) -> CGFloat {
    return a + (b - a) * t
}

func sceneAlpha(_ t: Double, _ start: Double, _ end: Double) -> CGFloat {
    let fade = 0.85
    let fadeIn = smoothstep(start, start + fade, t)
    let fadeOut = 1 - smoothstep(end - fade, end, t)
    return clamp(min(fadeIn, fadeOut))
}

func font(_ size: CGFloat, _ weight: NSFont.Weight = .regular) -> NSFont {
    if let pingFang = NSFont(name: weight.rawValue >= NSFont.Weight.semibold.rawValue ? "PingFangSC-Semibold" : "PingFangSC-Regular", size: size) {
        return pingFang
    }
    return NSFont.systemFont(ofSize: size, weight: weight)
}

func rgba(_ red: CGFloat, _ green: CGFloat, _ blue: CGFloat, _ alpha: CGFloat) -> NSColor {
    return NSColor(calibratedRed: red, green: green, blue: blue, alpha: alpha)
}

func drawText(
    _ text: String,
    rect: CGRect,
    size: CGFloat,
    weight: NSFont.Weight = .regular,
    color: NSColor = Palette.ink,
    alignment: NSTextAlignment = .left,
    lineSpacing: CGFloat = 8
) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = alignment
    paragraph.lineSpacing = lineSpacing
    paragraph.lineBreakMode = .byWordWrapping

    let attributes: [NSAttributedString.Key: Any] = [
        .font: font(size, weight),
        .foregroundColor: color,
        .paragraphStyle: paragraph,
        .kern: 0
    ]
    (text as NSString).draw(in: rect, withAttributes: attributes)
}

func drawCenteredText(_ text: String, centerY: CGFloat, width: CGFloat, size: CGFloat, weight: NSFont.Weight = .regular, color: NSColor = Palette.ink, lineSpacing: CGFloat = 8) {
    drawText(
        text,
        rect: CGRect(x: (CGFloat(width) - width) / 2, y: centerY - size * 0.75, width: width, height: size * 2.2),
        size: size,
        weight: weight,
        color: color,
        alignment: .center,
        lineSpacing: lineSpacing
    )
}

func roundedRect(_ rect: CGRect, radius: CGFloat, fill: NSColor, stroke: NSColor? = nil, lineWidth: CGFloat = 1) {
    let path = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
    fill.setFill()
    path.fill()
    if let stroke {
        stroke.setStroke()
        path.lineWidth = lineWidth
        path.stroke()
    }
}

func withAlpha(_ alpha: CGFloat, _ draw: () -> Void) {
    if alpha <= 0.001 {
        return
    }
    NSGraphicsContext.saveGraphicsState()
    if let context = NSGraphicsContext.current?.cgContext {
        context.setAlpha(alpha)
        context.beginTransparencyLayer(auxiliaryInfo: nil)
    }
    draw()
    NSGraphicsContext.current?.cgContext.endTransparencyLayer()
    NSGraphicsContext.restoreGraphicsState()
}

func drawShadowedCard(_ rect: CGRect, radius: CGFloat = 28, fill: NSColor = Palette.panel, stroke: NSColor = Palette.border) {
    NSGraphicsContext.saveGraphicsState()
    let shadow = NSShadow()
    shadow.shadowColor = rgba(0.05, 0.08, 0.16, 0.10)
    shadow.shadowBlurRadius = 34
    shadow.shadowOffset = NSSize(width: 0, height: -12)
    shadow.set()
    roundedRect(rect, radius: radius, fill: fill)
    NSGraphicsContext.restoreGraphicsState()
    roundedRect(rect, radius: radius, fill: fill, stroke: stroke)
}

func drawPill(_ rect: CGRect, text: String, color: NSColor, textColor: NSColor = Palette.blue) {
    roundedRect(rect, radius: rect.height / 2, fill: color)
    drawText(text, rect: rect.insetBy(dx: 18, dy: 8), size: 22, weight: .medium, color: textColor, alignment: .center, lineSpacing: 0)
}

func drawLogoMark(_ rect: CGRect, alpha: CGFloat = 1) {
    withAlpha(alpha) {
        let outer = NSBezierPath(roundedRect: rect, xRadius: rect.width * 0.28, yRadius: rect.width * 0.28)
        NSGraphicsContext.saveGraphicsState()
        outer.addClip()
        NSGradient(colors: [
            rgba(0.96, 0.98, 1.00, 0.98),
            rgba(0.91, 0.94, 1.00, 0.94)
        ])!.draw(in: rect, angle: -35)
        NSGraphicsContext.restoreGraphicsState()
        rgba(0.38, 0.52, 0.98, 0.36).setStroke()
        outer.lineWidth = max(1.2, rect.width * 0.014)
        outer.stroke()

        let leftX = rect.minX + rect.width * 0.13
        let baselineY = rect.minY + rect.height * 0.29
        let aiSize = rect.width * 0.30
        drawText(
            "AI",
            rect: CGRect(x: leftX, y: baselineY, width: rect.width * 0.42, height: rect.height * 0.40),
            size: aiSize,
            weight: .bold,
            color: Palette.blue,
            alignment: .center,
            lineSpacing: 0
        )

        let qRect = CGRect(
            x: rect.minX + rect.width * 0.61,
            y: rect.minY + rect.height * 0.31,
            width: rect.width * 0.24,
            height: rect.width * 0.24
        )
        let qPath = NSBezierPath(ovalIn: qRect)
        Palette.purple.setStroke()
        qPath.lineWidth = max(3, rect.width * 0.055)
        qPath.stroke()

        let tail = NSBezierPath()
        tail.move(to: CGPoint(x: qRect.maxX - qRect.width * 0.18, y: qRect.minY + qRect.height * 0.20))
        tail.line(to: CGPoint(x: qRect.maxX + qRect.width * 0.12, y: qRect.minY - qRect.height * 0.08))
        Palette.blueSoft.setStroke()
        tail.lineWidth = max(3, rect.width * 0.060)
        tail.lineCapStyle = .round
        tail.stroke()

        roundedRect(
            CGRect(x: rect.minX + rect.width * 0.16, y: rect.minY + rect.height * 0.23, width: rect.width * 0.62, height: rect.width * 0.033),
            radius: rect.width * 0.018,
            fill: Palette.cyan.withAlphaComponent(0.50)
        )
    }
}

func renderLogoPreview(to url: URL) {
    let size = 1024
    guard
        let bitmap = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: size,
            pixelsHigh: size,
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .calibratedRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        ),
        let graphics = NSGraphicsContext(bitmapImageRep: bitmap)
    else {
        fatalError("Unable to create logo preview")
    }
    NSGraphicsContext.saveGraphicsState()
    graphics.shouldAntialias = true
    graphics.imageInterpolation = .high
    NSGraphicsContext.current = graphics
    NSColor.clear.setFill()
    NSRect(x: 0, y: 0, width: size, height: size).fill()
    drawLogoMark(CGRect(x: 128, y: 128, width: 768, height: 768))
    graphics.flushGraphics()
    NSGraphicsContext.restoreGraphicsState()
    guard let cgImage = bitmap.cgImage else {
        fatalError("Unable to create logo CGImage")
    }
    writePoster(cgImage, to: url)
}

func drawBackground(t: Double) {
    let bounds = CGRect(x: 0, y: 0, width: width, height: height)
    let base = NSGradient(colors: [
        rgba(0.985, 0.992, 1.0, 1),
        rgba(0.94, 0.965, 1.0, 1),
        rgba(0.985, 0.985, 1.0, 1)
    ])!
    base.draw(in: bounds, angle: -90)

    let glowSpecs: [(CGFloat, CGFloat, CGFloat, NSColor)] = [
        (260 + 24 * sin(CGFloat(t) * 0.42), 180 + 18 * cos(CGFloat(t) * 0.34), 520, rgba(0.10, 0.33, 0.96, 0.16)),
        (1640 + 34 * cos(CGFloat(t) * 0.35), 220 + 24 * sin(CGFloat(t) * 0.3), 610, rgba(0.50, 0.28, 0.95, 0.13)),
        (1180 + 30 * sin(CGFloat(t) * 0.22), 910 + 16 * cos(CGFloat(t) * 0.42), 600, rgba(0.05, 0.72, 0.82, 0.10))
    ]
    for (cx, cy, radius, color) in glowSpecs {
        let path = NSBezierPath(ovalIn: CGRect(x: cx - radius / 2, y: cy - radius / 2, width: radius, height: radius))
        let gradient = NSGradient(colors: [color, color.withAlphaComponent(0)])!
        gradient.draw(in: path, relativeCenterPosition: .zero)
    }

    NSColor(calibratedRed: 0.72, green: 0.82, blue: 0.96, alpha: 0.18).setStroke()
    let linePath = NSBezierPath()
    let spacing: CGFloat = 88
    for x in stride(from: CGFloat(0), through: CGFloat(width), by: spacing) {
        linePath.move(to: CGPoint(x: x, y: 0))
        linePath.line(to: CGPoint(x: x, y: CGFloat(height)))
    }
    for y in stride(from: CGFloat(0), through: CGFloat(height), by: spacing) {
        linePath.move(to: CGPoint(x: 0, y: y))
        linePath.line(to: CGPoint(x: CGFloat(width), y: y))
    }
    linePath.lineWidth = 1
    linePath.stroke()
}

func drawScene1(t: Double) {
    let a = sceneAlpha(t, 0, 5)
    withAlpha(a) {
        let p = easeOut(smoothstep(0.1, 2.8, t))
        let topOffset = lerp(28, 0, p)
        func bottomY(top: CGFloat, height itemHeight: CGFloat) -> CGFloat {
            return CGFloat(height) - top - itemHeight
        }
        drawLogoMark(CGRect(x: 916, y: bottomY(top: 320 + topOffset, height: 88), width: 88, height: 88))
        drawText("AI QA Community", rect: CGRect(x: 500, y: bottomY(top: 452 + topOffset, height: 90), width: 920, height: 90), size: 66, weight: .semibold, color: Palette.ink, alignment: .center)
        drawText("重新定义信息获取的方式", rect: CGRect(x: 500, y: bottomY(top: 556 + topOffset, height: 64), width: 920, height: 64), size: 34, weight: .regular, color: Palette.muted, alignment: .center)
        let lineWidth = 260 * smoothstep(1.0, 4.4, t)
        roundedRect(CGRect(x: 960 - lineWidth / 2, y: bottomY(top: 654, height: 3), width: lineWidth, height: 3), radius: 1.5, fill: rgba(0.10, 0.33, 0.96, 0.48))
    }
}

func drawFragment(_ rect: CGRect, label: String, progress: CGFloat, accent: NSColor) {
    drawShadowedCard(rect, radius: 18, fill: rgba(1, 1, 1, 0.72), stroke: rgba(0.70, 0.78, 0.92, 0.32))
    roundedRect(CGRect(x: rect.minX + 22, y: rect.minY + 22, width: rect.width * progress, height: 7), radius: 3.5, fill: accent.withAlphaComponent(0.72))
    roundedRect(CGRect(x: rect.minX + 22, y: rect.minY + 48, width: rect.width * 0.62, height: 7), radius: 3.5, fill: rgba(0.66, 0.73, 0.84, 0.34))
    drawText(label, rect: CGRect(x: rect.minX + 22, y: rect.minY + rect.height - 44, width: rect.width - 44, height: 28), size: 18, weight: .medium, color: Palette.muted)
}

func drawScene2(t: Double) {
    let a = sceneAlpha(t, 5, 11)
    withAlpha(a) {
        let local = t - 5
        let labels = ["课程资料", "讨论记录", "检索结果", "回答片段", "管理数据", "知识标签", "用户反馈", "历史问题"]
        for i in 0..<labels.count {
            let angle = CGFloat(i) / CGFloat(labels.count) * CGFloat.pi * 2
            let radius = CGFloat(260 + (i % 3) * 80)
            let drift = CGFloat(sin(local * 0.8 + Double(i))) * 18
            let x = 960 + cos(angle) * radius + drift - 120
            let y = 472 + sin(angle) * (radius * 0.58) + CGFloat(cos(local * 0.7 + Double(i))) * 16 - 104
            let appear = smoothstep(5.2 + Double(i) * 0.18, 7.2 + Double(i) * 0.18, t)
            withAlpha(appear) {
                drawFragment(CGRect(x: x, y: y, width: 240, height: 108), label: labels[i], progress: 0.45 + CGFloat(i % 4) * 0.12, accent: i % 2 == 0 ? Palette.blueSoft : Palette.purpleSoft)
            }
        }
        drawText("信息越来越多", rect: CGRect(x: 440, y: 785, width: 1040, height: 64), size: 50, weight: .semibold, color: Palette.ink, alignment: .center)
        drawText("真正有价值的答案却越来越难找", rect: CGRect(x: 440, y: 728, width: 1040, height: 54), size: 34, weight: .regular, color: Palette.muted, alignment: .center)
    }
}

func drawConnection(_ from: CGPoint, _ to: CGPoint, alpha: CGFloat = 1) {
    let path = NSBezierPath()
    path.move(to: from)
    let mid = CGPoint(x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 - 30)
    path.curve(to: to, controlPoint1: CGPoint(x: mid.x, y: from.y), controlPoint2: CGPoint(x: mid.x, y: to.y))
    rgba(0.13, 0.38, 0.95, 0.22 * alpha).setStroke()
    path.lineWidth = 2
    path.stroke()
}

func drawScene3(t: Double) {
    let a = sceneAlpha(t, 11, 18)
    withAlpha(a) {
        let local = t - 11
        let p = easeInOut(smoothstep(11.3, 16.6, t))
        let center = CGPoint(x: 960, y: 452)
        let nodes = [
            CGPoint(x: 420, y: 280), CGPoint(x: 1500, y: 286), CGPoint(x: 360, y: 616),
            CGPoint(x: 1548, y: 640), CGPoint(x: 620, y: 210), CGPoint(x: 1300, y: 214),
            CGPoint(x: 598, y: 690), CGPoint(x: 1324, y: 710)
        ]
        for (i, source) in nodes.enumerated() {
            let current = CGPoint(x: lerp(source.x, center.x + CGFloat((i % 2 == 0 ? -1 : 1) * (82 + i * 4)), p), y: lerp(source.y, center.y + CGFloat((i % 3 - 1) * 72), p))
            drawConnection(current, center, alpha: p)
            let size = CGFloat(28 + (i % 3) * 8)
            let color = i % 2 == 0 ? Palette.blueSoft : Palette.purpleSoft
            NSColor.white.setFill()
            NSBezierPath(ovalIn: CGRect(x: current.x - size / 2, y: current.y - size / 2, width: size, height: size)).fill()
            color.withAlphaComponent(0.85).setFill()
            NSBezierPath(ovalIn: CGRect(x: current.x - size / 4, y: current.y - size / 4, width: size / 2, height: size / 2)).fill()
        }
        drawShadowedCard(CGRect(x: 640, y: 308, width: 640, height: 292), radius: 34, fill: rgba(1, 1, 1, 0.88), stroke: rgba(0.58, 0.68, 0.92, 0.34))
        drawLogoMark(CGRect(x: 902, y: 344, width: 116, height: 116))
        drawText("AI QA Community", rect: CGRect(x: 700, y: 486, width: 520, height: 54), size: 38, weight: .semibold, color: Palette.ink, alignment: .center)
        drawText("连接信息 · 理解内容 · 快速获得答案", rect: CGRect(x: 692, y: 548, width: 536, height: 40), size: 24, weight: .regular, color: Palette.muted, alignment: .center)

        let pulse = 0.5 + 0.5 * sin(CGFloat(local) * 2.3)
        roundedRect(CGRect(x: 735, y: 628, width: 450 * (0.72 + 0.28 * pulse), height: 4), radius: 2, fill: rgba(0.13, 0.38, 0.95, 0.22))
        drawText("帮助你连接信息、理解内容、快速获得答案", rect: CGRect(x: 420, y: 754, width: 1080, height: 58), size: 34, weight: .regular, color: Palette.muted, alignment: .center)
    }
}

func drawMetricLine(in rect: CGRect, phase: CGFloat, color: NSColor) {
    let path = NSBezierPath()
    let points = 46
    for i in 0..<points {
        let x = rect.minX + CGFloat(i) / CGFloat(points - 1) * rect.width
        let y = rect.midY + sin(CGFloat(i) * 0.45 + phase) * rect.height * 0.18 - CGFloat(i) / CGFloat(points) * rect.height * 0.16
        if i == 0 { path.move(to: CGPoint(x: x, y: y)) } else { path.line(to: CGPoint(x: x, y: y)) }
    }
    color.withAlphaComponent(0.74).setStroke()
    path.lineWidth = 3
    path.stroke()
}

func drawIcon(_ kind: Int, center: CGPoint, color: NSColor) {
    color.setStroke()
    color.setFill()
    let path = NSBezierPath()
    path.lineWidth = 3
    path.lineCapStyle = .round
    path.lineJoinStyle = .round
    if kind == 0 {
        NSBezierPath(ovalIn: CGRect(x: center.x - 18, y: center.y - 18, width: 36, height: 36)).stroke()
        path.move(to: CGPoint(x: center.x + 13, y: center.y + 13))
        path.line(to: CGPoint(x: center.x + 32, y: center.y + 32))
    } else if kind == 1 {
        for offset in [-20, 0, 20] {
            roundedRect(CGRect(x: center.x - 30, y: center.y + CGFloat(offset) - 8, width: 60, height: 16), radius: 8, fill: color.withAlphaComponent(0.12), stroke: color.withAlphaComponent(0.75), lineWidth: 2)
        }
    } else {
        let pts = [
            CGPoint(x: center.x - 30, y: center.y + 16),
            CGPoint(x: center.x, y: center.y - 18),
            CGPoint(x: center.x + 30, y: center.y + 16)
        ]
        path.move(to: pts[0]); path.line(to: pts[1]); path.line(to: pts[2])
        path.stroke()
        for point in pts {
            NSBezierPath(ovalIn: CGRect(x: point.x - 7, y: point.y - 7, width: 14, height: 14)).fill()
        }
    }
}

func drawScene4(t: Double) {
    let a = sceneAlpha(t, 18, 27)
    withAlpha(a) {
        drawText("核心能力，以更少步骤完成更多工作", rect: CGRect(x: 380, y: 186, width: 1160, height: 62), size: 42, weight: .semibold, color: Palette.ink, alignment: .center)
        let cardSpecs = [
            ("智能检索", "更快定位答案", Palette.blueSoft, 0),
            ("清晰管理", "结构化沉淀知识", Palette.purpleSoft, 1),
            ("高效协作", "让团队共享上下文", Palette.cyan, 2)
        ]
        for i in 0..<cardSpecs.count {
            let delay = 18.4 + Double(i) * 0.85
            let p = easeOut(smoothstep(delay, delay + 1.25, t))
            let x = CGFloat(290 + i * 452)
            let y = lerp(448, 384, p)
            let (title, subtitle, color, icon) = cardSpecs[i]
            withAlpha(p) {
                drawShadowedCard(CGRect(x: x, y: y, width: 392, height: 304), radius: 30, fill: rgba(1, 1, 1, 0.82), stroke: rgba(0.66, 0.74, 0.90, 0.36))
                drawIcon(icon, center: CGPoint(x: x + 76, y: y + 78), color: color)
                drawText(title, rect: CGRect(x: x + 48, y: y + 140, width: 296, height: 50), size: 36, weight: .semibold, color: Palette.ink)
                drawText(subtitle, rect: CGRect(x: x + 48, y: y + 198, width: 296, height: 36), size: 23, weight: .regular, color: Palette.muted)
                drawMetricLine(in: CGRect(x: x + 48, y: y + 244, width: 296, height: 42), phase: CGFloat(t) + CGFloat(i), color: color)
            }
        }
        drawText("智能检索    清晰管理    高效协作", rect: CGRect(x: 460, y: 790, width: 1000, height: 58), size: 34, weight: .medium, color: Palette.blue, alignment: .center)
    }
}

func drawWorkspacePanel(_ rect: CGRect, title: String, accent: NSColor, rows: Int) {
    drawShadowedCard(rect, radius: 24, fill: rgba(1, 1, 1, 0.78), stroke: rgba(0.66, 0.74, 0.90, 0.34))
    drawText(title, rect: CGRect(x: rect.minX + 28, y: rect.minY + 24, width: rect.width - 56, height: 36), size: 24, weight: .semibold, color: Palette.ink)
    for i in 0..<rows {
        let y = rect.minY + 82 + CGFloat(i) * 46
        roundedRect(CGRect(x: rect.minX + 28, y: y, width: rect.width - 56, height: 24), radius: 12, fill: i % 2 == 0 ? rgba(0.93, 0.96, 1, 0.92) : rgba(0.96, 0.94, 1, 0.82))
        roundedRect(CGRect(x: rect.minX + 28, y: y, width: (rect.width - 92) * (0.36 + CGFloat(i % 4) * 0.14), height: 24), radius: 12, fill: accent.withAlphaComponent(0.20))
    }
}

func drawScene5(t: Double) {
    let a = sceneAlpha(t, 27, 35)
    withAlpha(a) {
        let p = easeInOut(smoothstep(27.3, 31.5, t))
        drawText("适用于知识管理、业务查询、团队协作与数据分析", rect: CGRect(x: 390, y: 150, width: 1140, height: 64), size: 42, weight: .semibold, color: Palette.ink, alignment: .center)

        let shell = CGRect(x: 230, y: 282, width: 1460, height: 560)
        drawShadowedCard(shell, radius: 34, fill: rgba(1, 1, 1, 0.68), stroke: rgba(0.68, 0.76, 0.92, 0.36))
        drawPill(CGRect(x: shell.minX + 46, y: shell.minY + 42, width: 168, height: 48), text: "Workspace", color: rgba(0.90, 0.94, 1, 0.95), textColor: Palette.blue)
        drawText("AI QA Community", rect: CGRect(x: shell.midX - 210, y: shell.minY + 44, width: 420, height: 44), size: 28, weight: .semibold, color: Palette.ink, alignment: .center)

        drawWorkspacePanel(CGRect(x: 292, y: 402, width: 334, height: 318), title: "团队", accent: Palette.blueSoft, rows: 4)
        drawWorkspacePanel(CGRect(x: 686, y: 376, width: 548, height: 372), title: "搜索结果", accent: Palette.purpleSoft, rows: 5)
        drawWorkspacePanel(CGRect(x: 1292, y: 402, width: 334, height: 318), title: "数据面板", accent: Palette.cyan, rows: 4)

        let connectionPath = NSBezierPath()
        connectionPath.move(to: CGPoint(x: 626, y: 562))
        connectionPath.curve(to: CGPoint(x: 686, y: 562), controlPoint1: CGPoint(x: 650, y: 538), controlPoint2: CGPoint(x: 666, y: 538))
        connectionPath.move(to: CGPoint(x: 1234, y: 562))
        connectionPath.curve(to: CGPoint(x: 1292, y: 562), controlPoint1: CGPoint(x: 1254, y: 538), controlPoint2: CGPoint(x: 1270, y: 538))
        rgba(0.13, 0.38, 0.95, 0.24 + 0.12 * p).setStroke()
        connectionPath.lineWidth = 3
        connectionPath.stroke()

        let dotX = lerp(632, 1286, p)
        NSBezierPath(ovalIn: CGRect(x: dotX - 7, y: 555, width: 14, height: 14)).fill()
    }
}

func drawScene6(t: Double) {
    let a = sceneAlpha(t, 35, 42.4)
    withAlpha(a) {
        let p = easeOut(smoothstep(35.2, 38.4, t))
        let topOffset = lerp(34, 0, p)
        func bottomY(top: CGFloat, height itemHeight: CGFloat) -> CGFloat {
            return CGFloat(height) - top - itemHeight
        }
        drawLogoMark(CGRect(x: 894, y: bottomY(top: 284 + topOffset, height: 132), width: 132, height: 132))
        drawText("AI QA Community", rect: CGRect(x: 410, y: bottomY(top: 456 + topOffset, height: 82), width: 1100, height: 82), size: 62, weight: .semibold, color: Palette.ink, alignment: .center)
        drawText("让信息真正产生价值", rect: CGRect(x: 510, y: bottomY(top: 558 + topOffset, height: 56), width: 900, height: 56), size: 34, weight: .regular, color: Palette.muted, alignment: .center)
        withAlpha(smoothstep(38.2, 40.0, t)) {
            let ctaRect = CGRect(x: 840, y: bottomY(top: 660, height: 64), width: 240, height: 64)
            roundedRect(ctaRect, radius: 32, fill: Palette.blue)
            drawText("立即体验", rect: CGRect(x: ctaRect.minX, y: ctaRect.minY + 16, width: ctaRect.width, height: 36), size: 26, weight: .semibold, color: Palette.white, alignment: .center, lineSpacing: 0)
        }
    }
}

func renderImage(t: Double) -> CGImage {
    guard
        let bitmap = NSBitmapImageRep(
            bitmapDataPlanes: nil,
            pixelsWide: width,
            pixelsHigh: height,
            bitsPerSample: 8,
            samplesPerPixel: 4,
            hasAlpha: true,
            isPlanar: false,
            colorSpaceName: .calibratedRGB,
            bytesPerRow: 0,
            bitsPerPixel: 0
        ),
        let bitmapGraphics = NSGraphicsContext(bitmapImageRep: bitmap)
    else {
        fatalError("Unable to create bitmap render target")
    }

    NSGraphicsContext.saveGraphicsState()
    bitmapGraphics.shouldAntialias = true
    bitmapGraphics.imageInterpolation = .high
    NSGraphicsContext.current = bitmapGraphics
    drawBackground(t: t)
    drawScene1(t: t)
    drawScene2(t: t)
    drawScene3(t: t)
    drawScene4(t: t)
    drawScene5(t: t)
    drawScene6(t: t)
    bitmapGraphics.flushGraphics()
    NSGraphicsContext.restoreGraphicsState()

    guard let cgImage = bitmap.cgImage else {
        fatalError("Unable to create CGImage")
    }
    return cgImage
}

if CommandLine.arguments.count >= 4 && CommandLine.arguments[1] == "--still" {
    let stillTime = Double(CommandLine.arguments[2]) ?? 0
    let stillURL = URL(fileURLWithPath: CommandLine.arguments[3])
    try? FileManager.default.createDirectory(at: stillURL.deletingLastPathComponent(), withIntermediateDirectories: true)
    writePoster(renderImage(t: stillTime), to: stillURL)
    print("Wrote \(stillURL.path)")
    exit(0)
}

if CommandLine.arguments.count >= 3 && CommandLine.arguments[1] == "--logo" {
    let logoURL = URL(fileURLWithPath: CommandLine.arguments[2])
    try? FileManager.default.createDirectory(at: logoURL.deletingLastPathComponent(), withIntermediateDirectories: true)
    renderLogoPreview(to: logoURL)
    print("Wrote \(logoURL.path)")
    exit(0)
}

func makePixelBuffer(from cgImage: CGImage, adaptor: AVAssetWriterInputPixelBufferAdaptor) -> CVPixelBuffer {
    var maybeBuffer: CVPixelBuffer?
    guard let pool = adaptor.pixelBufferPool else {
        fatalError("Missing pixel buffer pool")
    }
    let status = CVPixelBufferPoolCreatePixelBuffer(nil, pool, &maybeBuffer)
    guard status == kCVReturnSuccess, let buffer = maybeBuffer else {
        fatalError("Unable to create pixel buffer")
    }

    CVPixelBufferLockBaseAddress(buffer, [])
    defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
    guard
        let baseAddress = CVPixelBufferGetBaseAddress(buffer),
        let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
        let context = CGContext(
            data: baseAddress,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
        )
    else {
        fatalError("Unable to create bitmap context")
    }
    context.interpolationQuality = .high
    context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
    return buffer
}

func writePoster(_ cgImage: CGImage, to url: URL) {
    guard let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        fatalError("Unable to create poster destination")
    }
    CGImageDestinationAddImage(destination, cgImage, nil)
    CGImageDestinationFinalize(destination)
}

let fileManager = FileManager.default
try? fileManager.createDirectory(at: outputURL.deletingLastPathComponent(), withIntermediateDirectories: true)
if fileManager.fileExists(atPath: outputURL.path) {
    try fileManager.removeItem(at: outputURL)
}
if fileManager.fileExists(atPath: posterURL.path) {
    try fileManager.removeItem(at: posterURL)
}

let writer = try AVAssetWriter(outputURL: outputURL, fileType: .mp4)
let settings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoAverageBitRateKey: 16_000_000,
        AVVideoExpectedSourceFrameRateKey: fps,
        AVVideoMaxKeyFrameIntervalKey: fps * 2,
        AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel
    ]
]

let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
input.expectsMediaDataInRealTime = false

let attributes: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height,
    kCVPixelBufferCGImageCompatibilityKey as String: true,
    kCVPixelBufferCGBitmapContextCompatibilityKey as String: true
]

let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: attributes)
guard writer.canAdd(input) else {
    fatalError("Unable to add video input")
}
writer.add(input)
guard writer.startWriting() else {
    fatalError("Unable to start writing: \(writer.error?.localizedDescription ?? "unknown error")")
}
writer.startSession(atSourceTime: .zero)

let posterFrame = Int((2.4 / speedFactor) * Double(fps))

for frameIndex in 0..<totalFrames {
    while !input.isReadyForMoreMediaData {
        Thread.sleep(forTimeInterval: 0.001)
    }
    autoreleasepool {
        let t = Double(frameIndex) / Double(fps) * speedFactor
        let cgImage = renderImage(t: t)
        if frameIndex == posterFrame {
            writePoster(cgImage, to: posterURL)
        }
        let pixelBuffer = makePixelBuffer(from: cgImage, adaptor: adaptor)
        let time = CMTime(value: CMTimeValue(frameIndex), timescale: fps)
        if !adaptor.append(pixelBuffer, withPresentationTime: time) {
            fatalError("Unable to append frame \(frameIndex): \(writer.error?.localizedDescription ?? "unknown error")")
        }
    }
    if frameIndex % 300 == 0 {
        print("Rendered frame \(frameIndex)/\(totalFrames)")
    }
}

input.markAsFinished()
let semaphore = DispatchSemaphore(value: 0)
writer.finishWriting {
    semaphore.signal()
}
semaphore.wait()

guard writer.status == .completed else {
    fatalError("Encoding failed: \(writer.error?.localizedDescription ?? "unknown error")")
}

print("Wrote \(outputURL.path)")
print("Wrote \(posterURL.path)")
print("Duration: \(durationSeconds)s at \(speedFactor)x, \(width)x\(height), \(fps)fps")
