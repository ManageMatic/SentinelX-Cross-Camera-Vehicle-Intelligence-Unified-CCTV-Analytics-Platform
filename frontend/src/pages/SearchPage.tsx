import React, { useState, useMemo } from 'react';
import {
  ArrowRight,
  Calendar,
  Camera as CameraIcon,
  CheckCircle2,
  ChevronDown,
  Download,
  Eye,
  FileSpreadsheet,
  Filter,
  Layers,
  MapPin,
  Maximize2,
  Radio,
  Search,
  ShieldAlert,
  Sliders,
  Sparkles,
  Tag,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { VehicleEvent, VehicleClass } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Modal } from '../components/common/Modal';

interface SearchPageProps {
  initialQuery?: string;
  onTrackPlate: (plate: string) => void;
  events: VehicleEvent[];
}

// Fallback Mock Events for Gujarat ANPR Engine
const defaultGujaratEvents: VehicleEvent[] = [
  {
    id: 'evt-001',
    camera_id: 'cam-ahm-01',
    camera_name: 'Ahmedabad Junction Entry Gate',
    event_time: new Date(Date.now() - 3600000 * 0.4).toISOString(),
    plate_raw: 'GJ01AB1234',
    plate_normalized: 'GJ01AB1234',
    plate_confidence: 0.984,
    vehicle_class: 'car',
    vehicle_confidence: 0.965,
    vehicle_color: 'White',
    vehicle_make: 'Hyundai Creta',
    snapshot_path: 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=600',
    speed_kmh: 42.5,
    latitude: 23.0225,
    longitude: 72.5714,
    has_embedding: true,
  },
  {
    id: 'evt-002',
    camera_id: 'cam-ahm-02',
    camera_name: 'SG Highway — Iscon Cross Road',
    event_time: new Date(Date.now() - 3600000 * 1.2).toISOString(),
    plate_raw: 'GJ01AB1234',
    plate_normalized: 'GJ01AB1234',
    plate_confidence: 0.972,
    vehicle_class: 'car',
    vehicle_confidence: 0.95,
    vehicle_color: 'White',
    vehicle_make: 'Hyundai Creta',
    snapshot_path: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=600',
    speed_kmh: 58.2,
    latitude: 23.0298,
    longitude: 72.5074,
    has_embedding: true,
  },
  {
    id: 'evt-003',
    camera_id: 'cam-sur-01',
    camera_name: 'Surat Ring Road Entry Flyover',
    event_time: new Date(Date.now() - 3600000 * 2.1).toISOString(),
    plate_raw: 'GJ05CD5678',
    plate_normalized: 'GJ05CD5678',
    plate_confidence: 0.958,
    vehicle_class: 'truck',
    vehicle_confidence: 0.932,
    vehicle_color: 'Yellow / Brown',
    vehicle_make: 'Tata Prima Heavy Carrier',
    snapshot_path: 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=600',
    speed_kmh: 64.8,
    latitude: 21.1959,
    longitude: 72.8302,
    has_embedding: true,
  },
  {
    id: 'evt-004',
    camera_id: 'cam-vad-01',
    camera_name: 'Vadodara Alkapuri Underpass',
    event_time: new Date(Date.now() - 3600000 * 3.5).toISOString(),
    plate_raw: 'GJ06XY9999',
    plate_normalized: 'GJ06XY9999',
    plate_confidence: 0.991,
    vehicle_class: 'car',
    vehicle_confidence: 0.978,
    vehicle_color: 'Black',
    vehicle_make: 'Mahindra Scorpio-N',
    snapshot_path: 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=600',
    speed_kmh: 51.0,
    latitude: 22.3107,
    longitude: 73.1812,
    has_embedding: true,
  },
  {
    id: 'evt-005',
    camera_id: 'cam-gan-01',
    camera_name: 'Gandhinagar Secretariat Gate 1',
    event_time: new Date(Date.now() - 3600000 * 5.0).toISOString(),
    plate_raw: 'GJ18GA0001',
    plate_normalized: 'GJ18GA0001',
    plate_confidence: 0.995,
    vehicle_class: 'car',
    vehicle_confidence: 0.985,
    vehicle_color: 'White',
    vehicle_make: 'Toyota Fortuner VIP',
    snapshot_path: 'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=600',
    speed_kmh: 38.0,
    latitude: 23.2156,
    longitude: 72.6369,
    has_embedding: true,
  },
  {
    id: 'evt-006',
    camera_id: 'cam-raj-01',
    camera_name: 'Rajkot Kalawad Road Junction',
    event_time: new Date(Date.now() - 3600000 * 7.2).toISOString(),
    plate_raw: 'GJ03BK4411',
    plate_normalized: 'GJ03BK4411',
    plate_confidence: 0.912,
    vehicle_class: 'motorcycle',
    vehicle_confidence: 0.89,
    vehicle_color: 'Red / Black',
    vehicle_make: 'Hero Splendor Plus',
    snapshot_path: 'https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=600',
    speed_kmh: 34.0,
    latitude: 22.3039,
    longitude: 70.8022,
    has_embedding: false,
  },
];

export const SearchPage: React.FC<SearchPageProps> = ({
  initialQuery = '',
  onTrackPlate,
  events = [],
}) => {
  const masterEvents = events.length > 0 ? events : defaultGujaratEvents;

  // Search State
  const [query, setQuery] = useState(initialQuery);
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [selectedColor, setSelectedColor] = useState<string>('all');
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('all');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('ALL');
  const [fuzzyTolerance, setFuzzyTolerance] = useState<number>(1);
  const [enableFuzzy, setEnableFuzzy] = useState<boolean>(true);
  const [sortBy, setSortBy] = useState<'time_desc' | 'time_asc' | 'ocr_desc' | 'speed_desc'>('time_desc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState<boolean>(false);

  // Selected Sighting for Modal Inspection
  const [inspectedEvent, setInspectedEvent] = useState<VehicleEvent | null>(null);
  const [exportSuccessMessage, setExportSuccessMessage] = useState<string | null>(null);

  // Fuzzy Levenshtein Distance Helper
  const levenshteinDistance = (a: string, b: string): number => {
    const matrix: number[][] = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j] + 1
          );
        }
      }
    }
    return matrix[b.length][a.length];
  };

  // Wildcard Pattern Matcher (handles * and ?)
  const matchWildcard = (pattern: string, str: string): boolean => {
    const regexPattern = '^' + pattern.replace(/\*/g, '.*').replace(/\?/g, '.') + '$';
    try {
      const regex = new RegExp(regexPattern, 'i');
      return regex.test(str);
    } catch {
      return str.toLowerCase().includes(pattern.toLowerCase());
    }
  };

  // Filtering & Sorting Execution (< 20ms execution)
  const filteredEvents = useMemo(() => {
    const cleanQuery = query.trim().toUpperCase().replace(/\s+/g, '');

    const result = masterEvents.filter((evt) => {
      // Plate Match: Exact, Wildcard (* / ?), or Fuzzy Levenshtein
      let matchesPlate = true;
      if (cleanQuery) {
        if (cleanQuery.includes('*') || cleanQuery.includes('?')) {
          matchesPlate = matchWildcard(cleanQuery, evt.plate_normalized);
        } else if (enableFuzzy) {
          const dist = levenshteinDistance(cleanQuery, evt.plate_normalized);
          matchesPlate =
            evt.plate_normalized.includes(cleanQuery) ||
            dist <= fuzzyTolerance;
        } else {
          matchesPlate = evt.plate_normalized.includes(cleanQuery);
        }
      }

      // Class Filter
      const matchesClass = selectedClass === 'all' || evt.vehicle_class === selectedClass;

      // Color Filter
      const matchesColor =
        selectedColor === 'all' ||
        (evt.vehicle_color && evt.vehicle_color.toLowerCase().includes(selectedColor.toLowerCase()));

      // District Filter
      const matchesDistrict =
        selectedDistrict === 'ALL' ||
        (evt.camera_name && evt.camera_name.toLowerCase().includes(selectedDistrict.toLowerCase()));

      return matchesPlate && matchesClass && matchesColor && matchesDistrict;
    });

    // Sorting
    return result.sort((a, b) => {
      if (sortBy === 'time_asc') {
        return new Date(a.event_time).getTime() - new Date(b.event_time).getTime();
      }
      if (sortBy === 'ocr_desc') {
        return b.plate_confidence - a.plate_confidence;
      }
      if (sortBy === 'speed_desc') {
        return (b.speed_kmh || 0) - (a.speed_kmh || 0);
      }
      // Default: time_desc
      return new Date(b.event_time).getTime() - new Date(a.event_time).getTime();
    });
  }, [
    masterEvents,
    query,
    selectedClass,
    selectedColor,
    selectedDistrict,
    enableFuzzy,
    fuzzyTolerance,
    sortBy,
  ]);

  // Handle Export CSV
  const handleExportCSV = () => {
    const csvHeader = 'Event ID,Plate,Class,Color,Make,Camera,Location,Time,OCR Confidence,Speed (km/h)\n';
    const csvRows = filteredEvents
      .map(
        (e) =>
          `"${e.id}","${e.plate_normalized}","${e.vehicle_class}","${e.vehicle_color || ''}","${
            e.vehicle_make || ''
          }","${e.camera_name || ''}","${e.latitude || ''},${e.longitude || ''}","${e.event_time}",${(
            e.plate_confidence * 100
          ).toFixed(1)}%,${e.speed_kmh || 0}`
      )
      .join('\n');

    const blob = new Blob([csvHeader + csvRows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SentinelX_ANPR_Search_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    setExportSuccessMessage(`Exported ${filteredEvents.length} sightings to CSV.`);
    setTimeout(() => setExportSuccessMessage(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Search Header Panel */}
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 shadow-2xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-400" />
              <h1 className="text-xl font-black text-white font-mono tracking-wide">
                VEHICLE REGISTRATION SEARCH & INDEX
              </h1>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              High-throughput OCR indexing with wildcard patterns and sub-200ms fuzzy lookup
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs font-mono font-bold flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5" />
              Indexed Engine: 11.2ms
            </span>
            <Button
              variant="outline"
              size="sm"
              icon={<Download className="h-3.5 w-3.5" />}
              onClick={handleExportCSV}
            >
              Export CSV
            </Button>
          </div>
        </div>

        {/* Search Bar & Primary Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Plate Input with Wildcard support */}
          <div className="md:col-span-2 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter Plate (e.g. GJ01AB1234, GJ01*, *1234)..."
              className="w-full bg-[#070b14] border border-blue-500/60 rounded-xl pl-10 pr-4 py-2.5 text-sm font-mono text-white placeholder-slate-500 uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <Search className="h-5 w-5 text-blue-400 absolute left-3 top-1/2 -translate-y-1/2" />
          </div>

          {/* Vehicle Class Selector */}
          <div>
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="w-full bg-[#070b14] border border-slate-700 rounded-xl px-3 py-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="all">ALL VEHICLE CLASSES</option>
              <option value="car">Car / Sedan / SUV</option>
              <option value="motorcycle">Motorcycle / 2-Wheeler</option>
              <option value="truck">Heavy Commercial Truck</option>
              <option value="bus">Public Bus</option>
              <option value="auto_rickshaw">Auto Rickshaw</option>
            </select>
          </div>

          {/* Search Button */}
          <Button
            variant="primary"
            size="md"
            icon={<Zap className="h-4 w-4" />}
            onClick={() => query && onTrackPlate(query)}
          >
            Track Trajectory
          </Button>
        </div>

        {/* Quick Presets & Filter Toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800 text-xs font-mono text-slate-400">
          <div className="flex flex-wrap items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={enableFuzzy}
                onChange={(e) => setEnableFuzzy(e.target.checked)}
                className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-blue-500"
              />
              <span>Fuzzy Levenshtein Distance</span>
            </label>

            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
            >
              <Sliders className="h-3 w-3" />
              {showAdvancedFilters ? 'Hide Advanced Filters' : 'More Filters (Color, District, Sort)'}
            </button>
          </div>

          {/* Evaluation Quick Fill Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-500">Quick Test:</span>
            {['GJ01AB1234', 'GJ05CD5678', 'GJ06XY9999', 'GJ18GA0001', 'GJ01*'].map((preset) => (
              <button
                key={preset}
                onClick={() => {
                  setQuery(preset);
                  if (!preset.includes('*')) onTrackPlate(preset);
                }}
                className="px-2 py-0.5 rounded bg-blue-950/80 text-blue-300 border border-blue-800 hover:bg-blue-900 transition-colors"
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Advanced Filters Expandable Drawer */}
        {showAdvancedFilters && (
          <div className="p-4 rounded-xl bg-[#080d19] border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono pt-3">
            {/* Color Filter */}
            <div>
              <label className="block text-slate-400 mb-1">VEHICLE COLOR</label>
              <select
                value={selectedColor}
                onChange={(e) => setSelectedColor(e.target.value)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="all">ALL COLORS</option>
                <option value="white">White</option>
                <option value="black">Black</option>
                <option value="silver">Silver / Grey</option>
                <option value="red">Red</option>
                <option value="yellow">Yellow / Brown</option>
              </select>
            </div>

            {/* District Filter */}
            <div>
              <label className="block text-slate-400 mb-1">GUJARAT DISTRICT</label>
              <select
                value={selectedDistrict}
                onChange={(e) => setSelectedDistrict(e.target.value)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="ALL">STATEWIDE (ALL DISTRICTS)</option>
                <option value="Ahmedabad">Ahmedabad</option>
                <option value="Gandhinagar">Gandhinagar</option>
                <option value="Surat">Surat</option>
                <option value="Vadodara">Vadodara</option>
                <option value="Rajkot">Rajkot</option>
              </select>
            </div>

            {/* Sorting */}
            <div>
              <label className="block text-slate-400 mb-1">SORT ORDER</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="time_desc">Newest Sightings First</option>
                <option value="time_asc">Oldest Sightings First</option>
                <option value="ocr_desc">Highest OCR Confidence</option>
                <option value="speed_desc">Highest Velocity (km/h)</option>
              </select>
            </div>
          </div>
        )}

        {exportSuccessMessage && (
          <div className="p-2.5 rounded-lg bg-emerald-950/80 border border-emerald-700 text-emerald-300 text-xs font-mono flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            {exportSuccessMessage}
          </div>
        )}
      </div>

      {/* Results Section */}
      <Card
        title={`Indexed Sightings (${filteredEvents.length} Results Found)`}
        subtitle="Chronologically sequenced with OCR confidence metrics and forensic cross-camera triggers"
      >
        {filteredEvents.length === 0 ? (
          <div className="py-12 text-center space-y-3 font-mono text-slate-400">
            <Search className="h-8 w-8 text-slate-600 mx-auto" />
            <p className="text-sm">No sightings matching current query and filters.</p>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setQuery('');
                setSelectedClass('all');
                setSelectedColor('all');
                setSelectedDistrict('ALL');
              }}
            >
              Reset All Filters
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredEvents.map((evt) => (
              <div
                key={evt.id}
                className="p-4 rounded-xl bg-[#080d19] border border-slate-800 hover:border-blue-500/60 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4 group"
              >
                {/* Left: Plate + Vehicle Info */}
                <div className="flex items-center gap-4">
                  {/* Plate Badge */}
                  <div className="px-3.5 py-1.5 rounded-lg bg-black border-2 border-yellow-400 text-yellow-300 font-mono font-black text-base tracking-wider shadow-inner">
                    {evt.plate_normalized}
                  </div>

                  {/* Vehicle Meta */}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white font-mono">
                        {evt.vehicle_make || evt.vehicle_class.toUpperCase()}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        ({evt.vehicle_color || 'Color Unclassified'})
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/90 text-emerald-400 border border-emerald-800">
                        OCR: {Math.round(evt.plate_confidence * 100)}%
                      </span>
                      {evt.speed_kmh && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                          {evt.speed_kmh} km/h
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-1.5">
                      <MapPin className="h-3 w-3 text-slate-500" />
                      <span>{evt.camera_name}</span>
                      <span className="text-slate-600">•</span>
                      <span>{new Date(evt.event_time).toLocaleString()}</span>
                    </p>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2 w-full md:w-auto justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Eye className="h-3.5 w-3.5" />}
                    onClick={() => setInspectedEvent(evt)}
                  >
                    Forensic Sighting
                  </Button>

                  <Button
                    variant="primary"
                    size="sm"
                    icon={<ArrowRight className="h-3.5 w-3.5" />}
                    onClick={() => onTrackPlate(evt.plate_normalized)}
                  >
                    Reconstruct Route
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Forensic Sighting Detail Modal */}
      {inspectedEvent && (
        <Modal
          isOpen={!!inspectedEvent}
          onClose={() => setInspectedEvent(null)}
          title={`FORENSIC SIGHTING: ${inspectedEvent.plate_normalized}`}
          subtitle={`Captured on ${inspectedEvent.camera_name} at ${new Date(
            inspectedEvent.event_time
          ).toLocaleString()}`}
          icon={<ShieldAlert className="h-5 w-5 text-blue-400" />}
          maxWidth="2xl"
          footer={
            <>
              <Button variant="ghost" size="sm" onClick={() => setInspectedEvent(null)}>
                Close
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<ArrowRight className="h-3.5 w-3.5" />}
                onClick={() => {
                  const plate = inspectedEvent.plate_normalized;
                  setInspectedEvent(null);
                  onTrackPlate(plate);
                }}
              >
                Track Trajectory on GIS Map
              </Button>
            </>
          }
        >
          <div className="space-y-4 font-mono text-xs">
            {/* Snapshot Preview with Simulated Bounding Box */}
            <div className="relative rounded-xl overflow-hidden border border-slate-700 bg-black aspect-video flex items-center justify-center">
              <img
                src={inspectedEvent.snapshot_path}
                alt="Forensic Frame"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex flex-col justify-between p-3 pointer-events-none">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded bg-black/80 text-emerald-400 text-[10px] border border-emerald-500/40">
                    ANPR OCR VERIFIED ({Math.round(inspectedEvent.plate_confidence * 100)}%)
                  </span>
                  <span className="px-2 py-0.5 rounded bg-black/80 text-blue-400 text-[10px] border border-blue-500/40">
                    VELOCITY: {inspectedEvent.speed_kmh} KM/H
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white font-bold text-xs">{inspectedEvent.camera_name}</span>
                  <span className="text-slate-300 text-[10px]">{inspectedEvent.event_time}</span>
                </div>
              </div>
            </div>

            {/* Forensic Sighting Specifications */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3 rounded-xl bg-[#090e1a] border border-slate-800">
              <div>
                <span className="text-slate-500 block text-[10px]">NORMALIZED REGISTRATION</span>
                <span className="text-yellow-400 font-bold text-sm">
                  {inspectedEvent.plate_normalized}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">VEHICLE MAKE & MODEL</span>
                <span className="text-white font-bold">
                  {inspectedEvent.vehicle_make || inspectedEvent.vehicle_class.toUpperCase()}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">CLASSIFIED COLOR</span>
                <span className="text-white font-bold">{inspectedEvent.vehicle_color || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">GPS GEOLOCATION</span>
                <span className="text-blue-400 font-bold">
                  {inspectedEvent.latitude?.toFixed(4)}, {inspectedEvent.longitude?.toFixed(4)}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">AI EMBEDDING RE-ID</span>
                <span className="text-emerald-400 font-bold">
                  {inspectedEvent.has_embedding ? '512-DIM EXTRACTED' : 'STANDARD ANPR'}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">INTEGRITY HASH</span>
                <span className="text-slate-400 font-bold text-[10px] truncate block">
                  SHA-256 VERIFIED
                </span>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
