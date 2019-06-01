package TTMp32Gme::LibraryHandler;

use strict;
use warnings;

use Path::Class;
use List::MoreUtils qw(uniq);
use Cwd;
use Data::Dumper;

use Image::Info qw(image_type);
use Music::Tag ( traditional => 1 );
use Music::Tag::Auto;
use Music::Tag::MusicBrainz;
use Music::Tag::MP3;
use Music::Tag::OGG;
use MP3::Tag;

#use Music::Tag:Amazon; #needs developer key
#use Music::Tag:LyricsFetcher; #maybe use this in a future release?

use Log::Message::Simple qw(msg debug error);

use TTMp32Gme::Build::FileHandler;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT =
	qw(updateTableEntry put_file_online createLibraryEntry get_album_list get_album get_album_online updateAlbum deleteAlbum cleanupAlbum replace_cover);

## private methods

sub oid_exist {
	my ( $oid, $dbh ) = @_;
	my @old_oids = map { @$_ } @{ $dbh->selectall_arrayref('SELECT oid FROM gme_library ORDER BY oid') };
	if ( grep( /^$oid$/, @old_oids ) ) {
		return 1;
	} else {
		return 0;
	}
}

sub newOID {
	my $dbh = $_[0];
	my $oid;
	my @old_oids =
		map { @$_ } @{ $dbh->selectall_arrayref('SELECT oid FROM gme_library ORDER BY oid DESC') };
	if (@old_oids) {
		if ( $old_oids[0] < 999 ) {

			#if we have free oids above the highest used oid, then use those
			$oid = $old_oids[0] + 1;
		} else {

			#if oid 999 is already in the database,
			#then look for oids freed by deleting old ones
			my %oid_test = map { $_ => 1 } @old_oids;
			my $new_oid  = $old_oids[-1] + 1;
			while ( ( $new_oid < 1001 ) and ( $oid_test{$new_oid} ) ) {
				$new_oid++;
			}
			if ( $new_oid == 1000 ) {

				#we still have not found a free oid,
				#look for free oids below the default oid
				$new_oid = $old_oids[-1] - 1;
				while ( $new_oid gt 0 and $oid_test{$new_oid} ) {
					$new_oid -= 1;
				}
				if ( $new_oid > 1 ) {
					$oid = $new_oid;
				} else {
					error( 'could not find a free oid.' . ' Try deleting oids from your library.', 1 );
				}
			} else {
				$oid = $new_oid;
			}
		}
	} else {
		$oid = 920;
	}
	return $oid;
}

sub writeToDatabase {
	my ( $table, $data, $dbh ) = @_;
	my @fields = sort keys %$data;
	my @values = @{$data}{@fields};
	my $query =
		sprintf( "INSERT INTO $table (%s) VALUES (%s)", join( ", ", @fields ), join( ", ", map { '?' } @values ) );
	my $qh = $dbh->prepare($query);
	$qh->execute(@values);
}

sub get_tracks {
	my ( $album, $dbh ) = @_;
	my $query  = "SELECT * FROM tracks WHERE parent_oid=$album->{'oid'} ORDER BY track";
	my $tracks = $dbh->selectall_hashref( $query, 'track' );
	foreach my $track ( sort keys %{$tracks} ) {
		$album->{ 'track_' . $track } = $tracks->{$track};
	}
	return $album;
}

sub put_cover_online {
	my ( $album, $httpd ) = @_;
	if ( $album->{'picture_filename'} ) {
		my $picture_file = file( $album->{'path'}, $album->{'picture_filename'} );
		my $online_path  = '/assets/images/' . $album->{'oid'} . '/' . $album->{'picture_filename'};
		put_file_online( $picture_file, $online_path, $httpd );
		return 1;
	} else {
		return 0;
	}
}

sub switchTracks {
	my ( $oid, $new_tracks, $dbh ) = @_;
	my $query  = "SELECT * FROM tracks WHERE parent_oid=$oid ORDER BY track";
	my $tracks = $dbh->selectall_hashref( $query, 'track' );
	$dbh->do("DELETE FROM tracks WHERE parent_oid=$oid");
	foreach my $track ( sort keys %{$new_tracks} ) {
		$tracks->{$track}{'track'} = $new_tracks->{$track};
		writeToDatabase( 'tracks', $tracks->{$track}, $dbh );
	}
}

sub sortByDiscTrackFilename {
	no warnings 'uninitialized';
	$a->{'disc'} <=> $b->{'disc'} or $a->{'track'} <=> $b->{'track'} or $a->{'filename'} cmp $b->{'filename'};
}

sub sortTracks {
	my ($track_data) = @_;
	my @tracks            = map( $_->{'track'}, @{$track_data} );
	my @sorted_track_data = sort sortByDiscTrackFilename @{$track_data};
	foreach my $track_no ( 0 .. $#sorted_track_data ) {
		$sorted_track_data[$track_no]->{'track'} = $track_no + 1;
	}
	return @sorted_track_data;
}

## public methods:

sub updateTableEntry {
	my ( $table, $keyname, $search_keys, $data, $dbh ) = @_;
	my @fields = sort keys %$data;
	my @values = @{$data}{@fields};
	my $qh     = $dbh->prepare( sprintf( 'UPDATE %s SET %s=? WHERE %s', $table, join( "=?, ", @fields ), $keyname ) );
	push( @values, @{$search_keys} );
	$qh->execute(@values);
	return !$dbh->errstr;
}

sub put_file_online {
	my ( $file, $online_path, $httpd ) = @_;
	$httpd->reg_cb(
		$online_path => sub {
			my $file_data = $file->slurp( iomode => '<:raw' );
			my ( $httpd, $req ) = @_;
			$req->respond( { content => [ '', $file_data ] } );
		}
	);
	return 1;
}

sub createLibraryEntry {
	my ( $albumList, $dbh, $debug ) = @_;
	foreach my $album ( @{$albumList} ) {
		if ($album) {
			my $oid = newOID($dbh);
			my %album_data;
			my @track_data;
			my $pictureData;
			my $trackNo = 1;
			foreach my $fileId ( sort keys %{$album} ) {
				if ( $album->{$fileId} =~ /\.(mp3|ogg)$/i ) {
					if ($debug) { debug( "Parsing audio file: $album->{$fileId}", $debug ); }

					#handle mp3 and ogg audio files
					my $info = Music::Tag->new( $album->{$fileId} );
					$info->get_tag( $album->{$fileId} );

					#if ($debug) {print 'Music::Tag::get_tag returned:' . Dumper($info);}

					#fill in album info
					if ( !$album_data{'album_title'} && $info->album() ) {
						$album_data{'album_title'} = $info->album();
						$album_data{'path'}        = cleanup_filename( $album_data{'album_title'} );
					}
					if ( !$album_data{'album_artist'} && $info->albumartist() ) {
						$album_data{'album_artist'} = $info->albumartist();
					} elsif ( !$album_data{'album_artist'} && $info->artist() ) {
						$album_data{'album_artist'} = $info->artist();
					}
					if ( !$album_data{'album_year'} && $info->year() ) {
						$album_data{'album_year'} = $info->get_year();
					}
					if ( !$album_data{'picture_filename'} && $info->picture_exists() ) {
						if ( $info->picture_filename() ) {
							$album_data{'picture_filename'} = cleanup_filename( $info->picture_filename() );
						} elsif ( $info->picture() ) {
							my $pic = $info->picture();
							$pictureData = $$pic{'_Data'};
							my $mimetype = $$pic{'MIME type'};
							$album_data{'picture_filename'} = get_cover_filename($mimetype, $pictureData);
						}
					} elsif ( !$album_data{'picture_filename'}
						&& !$info->picture_exists()
						&& $album->{$fileId} =~ /\.mp3$/i )
					{
						#Music::Tag::MP3 is not always reliable when extracting the picture,
						#try to use MP3::Tag directly.
						my $mp3 = MP3::Tag->new( $album->{$fileId} );
						$mp3->get_tags();

						if ($debug) { print Dumper($mp3); }
						my $id3v2_tagdata = $mp3->{ID3v2};
						if ($id3v2_tagdata) {
							my $apic = $id3v2_tagdata->get_frame("APIC");
							$pictureData = $$apic{'_Data'};
							my $mimetype = $$apic{'MIME type'};
							$album_data{'picture_filename'} = get_cover_filename($mimetype, $pictureData);
						}
					}

					#fill in track info
					my %trackInfo = (
						'parent_oid' => $oid,
						'album'      => $info->album(),
						'artist'     => $info->artist(),
						'disc'       => $info->disc(),
						'duration'   => $info->duration(),
						'genre'      => $info->genre(),
						'lyrics'     => $info->lyrics(),
						'title'      => $info->title(),
						'track'      => $info->track(),
						'filename'   => $album->{$fileId},
					);
					if ( !$trackInfo{'track'} ) {
						$trackInfo{'track'} = $trackNo;
						$trackNo++;
						$trackInfo{'title'} = cleanup_filename( ( file( $album->{$fileId} ) )->basename() );
						error(
"No useable id3 info found in $album->{$fileId}.\nPlease add an id3v2 tag to your mp3 file in order to get proper album and track info."
						);
					}
					push( @track_data, \%trackInfo );
				} elsif ( $album->{$fileId} =~ /\.(jpg|jpeg|tif|tiff|png|gif)$/i ) {
					if ($debug) { debug( "Parsing cover image: $album->{$fileId}", $debug ); }

					#handle pictures
					my $picture_file = file( $album->{$fileId} );
					$pictureData = $picture_file->slurp( iomode => '<:raw' );
					$album_data{'picture_filename'} = cleanup_filename( $picture_file->basename() );
				}
			}
			$album_data{'oid'}        = $oid;
			$album_data{'num_tracks'} = scalar(@track_data);
			if ( !$album_data{'album_title'} ) {
				$album_data{'path'}        = 'unknown';
				$album_data{'album_title'} = $album_data{'path'};
			}
			$album_data{'path'} = makeNewAlbumDir( $album_data{'path'} );
			if ( $album_data{'picture_filename'} and $pictureData ) {
				my $picture_file =
					file( $album_data{'path'}, $album_data{'picture_filename'} );
				$picture_file->spew( iomode => '>:raw', $pictureData );
			}
			@track_data = sortTracks( \@track_data );
			foreach my $track (@track_data) {
				$track->{'filename'} =
					moveToAlbum( $album_data{'path'}, $track->{'filename'} );
				writeToDatabase( 'tracks', $track, $dbh );
			}
			writeToDatabase( 'gme_library', \%album_data, $dbh );
			if ($debug) {
				debug( "Found the following album info:\n",   $debug );
				debug( Dumper( \%album_data ),                $debug );
				debug( "\nFound the following track info:\n", $debug );
				debug( Dumper( \@track_data ),                $debug );
			}
		}
	}
	removeTempDir();
}

sub get_cover_filename {
	my ( $mimetype, $pictureData ) = @_;
	if ( $mimetype =~ /^image/i ) {
		$mimetype =~ s/.*\///;
		return 'cover.' . $mimetype;
	} elsif ($pictureData) {
		my $imgType = image_type( \$pictureData );
		return 'cover.' . $imgType;
	}
	return 0;
}

sub get_album_list {
	my ( $dbh, $httpd, $debug ) = @_;
	my @albumList;
	my $albums         = $dbh->selectall_hashref( q( SELECT * FROM gme_library ORDER BY oid DESC ), 'oid' );
	my %gmes_on_tiptoi = get_gmes_already_on_tiptoi();
	if ($debug) { debug( 'Found gme files on tiptoi: ' . Dumper( \%gmes_on_tiptoi ), $debug ); }
	foreach my $oid ( sort keys %{$albums} ) {
		$albums->{$oid} = get_tracks( $albums->{$oid}, $dbh );
		if ( $albums->{$oid}->{'gme_file'} ) {
			$albums->{$oid}->{'gme_on_tiptoi'} = exists( $gmes_on_tiptoi{ $albums->{$oid}->{'gme_file'} } );
		} else {
			$albums->{$oid}->{'gme_on_tiptoi'} = 0;
		}
		put_cover_online( $albums->{$oid}, $httpd );
		push( @albumList, $albums->{$oid} );
	}
	return \@albumList;
}

sub get_album {
	my ( $oid, $dbh ) = @_;
	my $album = $dbh->selectrow_hashref( q( SELECT * FROM gme_library WHERE oid=? ), {}, $oid );
	$album = get_tracks( $album, $dbh );
	return $album;
}

sub get_album_online {
	my ( $oid, $httpd, $dbh ) = @_;
	if ($oid) {
		my $album          = get_album( $oid, $dbh );
		my %gmes_on_tiptoi = get_gmes_already_on_tiptoi();
		$album->{'gme_on_tiptoi'} = exists( $gmes_on_tiptoi{ $album->{'gme_file'} } );
		put_cover_online( $album, $httpd );
		return $album;
	}
	return 0;
}

sub updateAlbum {
	my ( $postData, $dbh ) = @_;
	my $old_oid = $postData->{'old_oid'};
	delete( $postData->{'old_oid'} );
	if ( $old_oid != $postData->{'oid'} ) {
		if ( oid_exist( $old_oid, $dbh ) ) {
			return 0;
			$dbh->set_err( '', 'Could not update album, oid already exists. Try a different oid.' );
		} else {
			for my $track ( grep /^track_/, keys %{$postData} ) {
				$postData->{$track}{'parent_oid'} = $postData->{'oid'};
			}
		}
	}
	my %new_tracks;
	for my $track ( sort grep /^track_/, keys %{$postData} ) {
		my $old_track = $track;
		$old_track =~ s/^track_//;
		$new_tracks{$old_track} = $postData->{$track}{'track'};
		delete( $postData->{$track}{'track'} );
		my %track_data = %{ $postData->{$track} };
		my @selectors  = ( $old_oid, $old_track );
		updateTableEntry( 'tracks', 'parent_oid=? and track=?', \@selectors, \%track_data, $dbh );
		delete( $postData->{$track} );
	}
	switchTracks( $postData->{'oid'}, \%new_tracks, $dbh );
	my @selector = ($old_oid);
	updateTableEntry( 'gme_library', 'oid=?', \@selector, $postData, $dbh );
	return $postData->{'oid'};
}

sub deleteAlbum {
	my ( $oid, $httpd, $dbh ) = @_;
	my $album_data = $dbh->selectrow_hashref( q(SELECT path,picture_filename FROM gme_library WHERE oid=?), {}, $oid );
	if ( $album_data->{'picture_filename'} ) {
		$httpd->unreg_cb( '/assets/images/' . $oid . '/' . $album_data->{'picture_filename'} );
	}
	if ( remove_library_dir( $album_data->{'path'} ) ) {
		$dbh->do( q(DELETE FROM tracks WHERE parent_oid=?), {}, $oid );
		$dbh->do( q( DELETE FROM gme_library WHERE oid=? ), {}, $oid );
	}
	return $oid;
}

sub cleanupAlbum {
	my ( $oid, $httpd, $dbh ) = @_;
	my $album_data = $dbh->selectrow_hashref( q(SELECT path,picture_filename FROM gme_library WHERE oid=?), {}, $oid );
	my $query      = q(SELECT filename FROM tracks WHERE parent_oid=? ORDER BY track);
	my @file_list =
		map { @$_ } @{ $dbh->selectall_arrayref( $query, {}, $oid ) };
	my $data = { 'filename' => undef };
	if ( clearAlbum( $album_data->{'path'}, \@file_list ) ) {
		updateTableEntry( 'tracks', 'parent_oid=?', [$oid], $data, $dbh );
	}
	return $oid;
}

sub replace_cover {
	my ( $oid, $filename, $file_data, $httpd, $dbh ) = @_;
	if ( $filename && $file_data ) {
		my $album_data = $dbh->selectrow_hashref( q(SELECT path,picture_filename FROM gme_library WHERE oid=?), {}, $oid );
		if ( $album_data->{'picture_filename'} ) {
			$httpd->unreg_cb( '/assets/images/' . $oid . '/' . $album_data->{'picture_filename'} );
			file( $album_data->{'path'}, $album_data->{'picture_filename'} )->remove();
			if ( $filename eq $album_data->{'picture_filename'} ) {

				#hack to make sure the cover is refreshed properly
				#despite browser caching.
				$filename = "0_$filename";
			}
		}
		my @selector = ($oid);
		$album_data->{'picture_filename'} = $filename;
		updateTableEntry( 'gme_library', 'oid=?', \@selector, $album_data, $dbh );
		my $picture_file =
			file( $album_data->{'path'}, $album_data->{'picture_filename'} );
		$picture_file->spew( iomode => '>:raw', $file_data );
		return $oid;
	} else {
		return 0;
	}
}

1;
