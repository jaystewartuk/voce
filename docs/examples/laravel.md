# A reservation sync in Laravel

A property manager lists the same flat on Airbnb, Vrbo and Booking.com. Each channel sends reservations in
its own shape, and the job below folds them into one table, keeps the nightly rate in minor units, and tells
the guest when the booking is confirmed. The code leans on PHP 8 features throughout: enums, readonly
properties, constructor promotion, `match`, the nullsafe operator `?->`, named arguments and attributes.

## The channel as an enum

A backed enum gives each channel a stable string for the database and a method for the fee it charges.
`Channel::from('vrbo')` throws on an unknown value; `Channel::tryFrom` returns `null` instead.

```php
<?php

namespace App\Enums;

enum Channel: string
{
    case Airbnb = 'airbnb';
    case Vrbo = 'vrbo';
    case Booking = 'booking';

    public function feePercent(): float
    {
        return match ($this) {
            self::Airbnb => 3.0,
            self::Vrbo => 5.0,
            self::Booking => 15.0,
        };
    }

    public static function fromHost(string $host): ?self
    {
        return match (true) {
            str_contains($host, 'airbnb') => self::Airbnb,
            str_contains($host, 'vrbo'), str_contains($host, 'homeaway') => self::Vrbo,
            str_ends_with($host, 'booking.com') => self::Booking,
            default => null,
        };
    }
}
```

## The model

The `$casts` array turns the channel column into the enum on the way out and back into a string on the way
in, and the dates into `Carbon` instances. `nights` is a computed attribute: `$reservation->nights` calls the
accessor. The scope `arriving()` reads as `Reservation::arriving(today())->get()`.

```php
<?php

namespace App\Models;

use App\Enums\Channel;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Support\Carbon;

class Reservation extends Model
{
    protected $fillable = ['channel', 'external_id', 'check_in', 'check_out', 'nightly_rate_cents', 'status'];

    protected $casts = [
        'channel' => Channel::class,
        'check_in' => 'date',
        'check_out' => 'date',
        'nightly_rate_cents' => 'integer',
    ];

    public function guest(): BelongsTo
    {
        return $this->belongsTo(Guest::class);
    }

    protected function nights(): Attribute
    {
        return Attribute::get(fn () => (int) $this->check_in->diffInDays($this->check_out));
    }

    protected function total(): Attribute
    {
        return Attribute::get(function (): int {
            $gross = $this->nights * $this->nightly_rate_cents;

            return (int) round($gross * (1 - $this->channel->feePercent() / 100));
        });
    }

    public function scopeArriving(Builder $query, Carbon $on): Builder
    {
        return $query->whereDate('check_in', $on)->where('status', '!=', 'cancelled');
    }
}
```

## The job

The job is queued with a backoff and gives up after three tries. The constructor's `readonly` promoted
properties are set once and never again. Each payload is normalised with `match` on the channel, then
`updateOrCreate` keyed on the channel and the channel's own id, so a resent payload updates the row instead
of duplicating it. The `?->` on `$guest` means a reservation with no guest row is skipped without an error.

```php
<?php

namespace App\Jobs;

use App\Enums\Channel;
use App\Models\Reservation;
use App\Notifications\BookingConfirmed;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\Attributes\WithoutRelations;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

#[WithoutRelations]
class SyncReservations implements ShouldQueue
{
    use Queueable;

    public int $tries = 3;

    /** @var array<int, int> */
    public array $backoff = [30, 120, 600];

    /**
     * @param  Collection<int, array<string, mixed>>  $payloads
     */
    public function __construct(
        public readonly Channel $channel,
        public readonly Collection $payloads,
    ) {}

    public function handle(): void
    {
        DB::transaction(function () {
            $this->payloads
                ->map(fn (array $payload) => $this->normalise($payload))
                ->filter()
                ->each(function (array $attributes) {
                    $reservation = Reservation::updateOrCreate(
                        ['channel' => $this->channel, 'external_id' => $attributes['external_id']],
                        $attributes,
                    );

                    if ($reservation->wasRecentlyCreated && $reservation->status === 'confirmed') {
                        $reservation->guest?->notify(new BookingConfirmed($reservation));
                    }
                });
        });
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return array<string, mixed>|null
     */
    protected function normalise(array $payload): ?array
    {
        [$in, $out, $rate] = match ($this->channel) {
            Channel::Airbnb => [$payload['start_date'], $payload['end_date'], $payload['nightly_price']['amount']],
            Channel::Vrbo => [$payload['arrival'], $payload['departure'], $payload['rate'] ?? null],
            Channel::Booking => [$payload['checkin'], $payload['checkout'], $payload['price'] / $payload['nights']],
        };

        if ($rate === null || $in >= $out) {
            return null;
        }

        return [
            'external_id' => (string) ($payload['id'] ?? $payload['reservation_id']),
            'check_in' => $in,
            'check_out' => $out,
            'nightly_rate_cents' => (int) round($rate * 100),
            'status' => Str::lower($payload['status'] ?? 'confirmed'),
        ];
    }
}
```

## Dispatching it

A controller method receives the webhook, works out the channel from the request's host, and dispatches the
job with named arguments. The `abort_unless` call returns a 422 when the host is not one we know.

```php
public function store(Request $request): JsonResponse
{
    $channel = Channel::fromHost($request->getHost());

    abort_unless($channel instanceof Channel, 422, 'Unknown channel');

    SyncReservations::dispatch(
        channel: $channel,
        payloads: collect($request->input('reservations', [])),
    )->onQueue('sync');

    return response()->json(['queued' => true], 202);
}
```

## A test

The test fakes the queue, posts a payload as Vrbo would, and asserts that the job was pushed with the right
channel. `Queue::assertPushed` takes a closure that receives the job, and the arrow function returns true when
the channel matches.

```php
public function test_a_vrbo_webhook_queues_a_sync(): void
{
    Queue::fake();

    $this->postJson('https://hooks.vrbo.com/reservations', ['reservations' => [
        ['reservation_id' => 'VR-42', 'arrival' => '2026-11-03', 'departure' => '2026-11-07', 'rate' => 180.00],
    ]])->assertStatus(202);

    Queue::assertPushed(SyncReservations::class, fn ($job) => $job->channel === Channel::Vrbo
        && $job->payloads->count() === 1);
}
```

Two things worth saying out loud. The fee is taken off in the model, so the figure a guest sees and the
figure the books see come from one place. And the job is idempotent: run it twice on the same payloads and
the table is the same afterwards, which is what you want from anything a webhook can retry.
