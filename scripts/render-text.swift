// Rasterize fixed artwork using the original macOS fonts, without bundling fonts.
import AppKit
import CoreText

let input = CommandLine.arguments[1]
let output = CommandLine.arguments[2]
let items = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input))) as! [[String: Any]]
for (index, item) in items.enumerated() {
    let size = item["size"] as! Double
    let family = item["family"] as! String
    var font = NSFont(name: family, size: size)!
    if item["bold"] as! Bool { font = NSFontManager.shared.convert(font, toHaveTrait: .boldFontMask) }
    if item["italic"] as! Bool { font = NSFontManager.shared.convert(font, toHaveTrait: .italicFontMask) }
    let string = NSAttributedString(string: item["text"] as! String, attributes: [.font: font, .foregroundColor: NSColor.white])
    let line = CTLineCreateWithAttributedString(string)
    let advance = CTLineGetTypographicBounds(line, nil, nil, nil)
    let bounds = CTLineGetBoundsWithOptions(line, [.useGlyphPathBounds])
    let width = ceil(max(advance, bounds.maxX) - min(0, bounds.minX) + 8)
    let height = ceil(max(item["linespace"] as! Double, bounds.height) + 8)
    try JSONSerialization.data(withJSONObject: ["advance": advance]).write(to: URL(fileURLWithPath: "\(output)/\(index).json"))
    let density: CGFloat = 4
    let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(width * density), pixelsHigh: Int(height * density), bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    let graphics = NSGraphicsContext(bitmapImageRep: bitmap)!
    NSGraphicsContext.current = graphics
    let context = graphics.cgContext
    context.scaleBy(x: density, y: density)
    context.setShouldAntialias(true)
    context.textPosition = CGPoint(x: (width - advance) / 2, y: height / 2 - (item["ascent"] as! Double - (item["descent"] as! Double)) / 2)
    CTLineDraw(line, context)
    NSGraphicsContext.restoreGraphicsState()
    try bitmap.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: "\(output)/\(index).png"))
}
