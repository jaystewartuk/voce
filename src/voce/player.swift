// voce's audio player: gapless playback, real pause and resume, and the exact position for the highlight.
// Reads commands on stdin and reports progress on stdout, one line each.
//   play ID PATH · pause · resume · stop · rate R · quit
// Events: pos ID SECONDS (every 50 ms while playing) · done ID · error MESSAGE
import AVFoundation
import Foundation

let engine = AVAudioEngine()
let node = AVAudioPlayerNode()
let pitch = AVAudioUnitTimePitch()
engine.attach(node)
engine.attach(pitch)
var format = AVAudioFormat(standardFormatWithSampleRate: 24000, channels: 1)!
engine.connect(node, to: pitch, format: format)
engine.connect(pitch, to: engine.mainMixerNode, format: format)

let lock = NSLock()
var generation = 0
var currentID = ""
var playing = false
var cache: [String: AVAudioPCMBuffer] = [:]

func emit(_ s: String) {
    FileHandle.standardOutput.write((s + "\n").data(using: .utf8)!)
}

func buffer(_ path: String) -> AVAudioPCMBuffer? {
    if let b = cache[path] { return b }
    guard let file = try? AVAudioFile(forReading: URL(fileURLWithPath: path)),
          let b = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: AVAudioFrameCount(file.length))
    else { return nil }
    do { try file.read(into: b) } catch { return nil }
    if cache.count > 64 { cache.removeAll() }
    cache[path] = b
    return b
}

func startEngine() -> Bool {
    if engine.isRunning { return true }
    do { try engine.start(); return true } catch { emit("error engine: \(error.localizedDescription)"); return false }
}

let timer = DispatchSource.makeTimerSource(queue: DispatchQueue.global())
timer.schedule(deadline: .now(), repeating: .milliseconds(50))
timer.setEventHandler {
    lock.lock(); let on = playing; let id = currentID; lock.unlock()
    guard on, let t = node.lastRenderTime, let p = node.playerTime(forNodeTime: t) else { return }
    emit(String(format: "pos %@ %.3f", id, max(0, Double(p.sampleTime) / p.sampleRate)))
}
timer.resume()

while let line = readLine() {
    let parts = line.split(separator: " ", maxSplits: 2).map(String.init)
    guard let cmd = parts.first else { continue }
    switch cmd {
    case "play" where parts.count == 3:
        let id = parts[1], path = parts[2]
        lock.lock(); generation += 1; let gen = generation; playing = false; lock.unlock()
        node.stop()
        guard let b = buffer(path) else { emit("error cannot read \(path)"); emit("done \(id)"); continue }
        if b.format != format {
            engine.disconnectNodeOutput(node)
            engine.connect(node, to: pitch, format: b.format)
            format = b.format
        }
        guard startEngine() else { emit("done \(id)"); continue }
        node.scheduleBuffer(b, at: nil, options: [], completionCallbackType: .dataPlayedBack) { _ in
            lock.lock(); let same = gen == generation; if same { playing = false }; lock.unlock()
            if same { emit("done \(id)") }
        }
        lock.lock(); currentID = id; playing = true; lock.unlock()
        node.play()
    case "pause":
        node.pause()
        lock.lock(); playing = false; lock.unlock()
    case "resume":
        if startEngine() { node.play(); lock.lock(); playing = true; lock.unlock() }
    case "stop":
        lock.lock(); generation += 1; playing = false; lock.unlock()
        node.stop()
    case "rate" where parts.count >= 2:
        pitch.rate = Float(parts[1]) ?? 1.0
    case "quit":
        node.stop(); engine.stop(); exit(0)
    default:
        emit("error unknown command \(line)")
    }
}
node.stop()
engine.stop()
